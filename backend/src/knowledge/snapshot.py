import json
import uuid
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.config import settings
from core.logging import logger
from core.errors import ManifestValidationError, KnowledgeSnapshotError
from schemas.knowledge import ManifestSchema, DocumentMetadata, SnapshotStatusResponse
from storage.local import LocalStorageAdapter
from retrieval.chunking import chunk_document


def strip_frontmatter(text: str) -> str:
    """
    Removes a leading YAML frontmatter block so it never reaches the prompt or the chunker.
    Returns the text unchanged when there is no frontmatter or the block is unterminated.
    """
    body = text.lstrip("\ufeff")
    lines = body.split("\n")
    if not lines or lines[0].strip() != "---":
        return text

    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "\n".join(lines[idx + 1:]).lstrip("\n")

    return text


class KnowledgeSnapshot:
    def __init__(
        self,
        version: str,
        created_at: str,
        manifest: ManifestSchema,
        documents_content: Dict[str, str],
        chunks: List[Dict[str, Any]]
    ):
        self.version = version
        self.created_at = created_at
        self.manifest = manifest
        self.documents_content = documents_content
        self.chunks = chunks
        self._full_context: Optional[str] = None
        self._language_contexts: Dict[str, str] = {}

    def get_full_context(self) -> str:
        """
        Assembles all approved documents into a unified markdown context for OKF.

        The result is memoised per snapshot: it can only change when SnapshotManager
        swaps in a new snapshot, so no TTL is needed. Keeping the string byte-identical
        across requests is also what lets the model reuse its cached prompt prefix.
        """
        if settings.cache_knowledge_context and self._full_context is not None:
            return self._full_context

        context_parts = []
        for doc_meta in self.manifest.documents:
            if doc_meta.enabled and doc_meta.id in self.documents_content:
                context_parts.append(
                    f"--- DOCUMENT: {doc_meta.title} (ID: {doc_meta.id}, Lang: {doc_meta.lang}) ---\n"
                    f"{self.documents_content[doc_meta.id]}\n"
                )

        context = "\n".join(context_parts)
        self._full_context = context
        return context

    def get_context_for_language(self, lang: str = "en") -> str:
        """
        Assembles a language-optimized, byte-identical knowledge context for OKF.

        - For English ('en'): includes only approved English documents, cutting ~48% prompt tokens
          by omitting redundant Hindi and Spanish translations.
        - For non-English ('hi', 'es'): includes approved localized documents where available
          and English documents as fallback for missing topics.
        - The resulting prompt prefix is memoized per language, maximizing KV cache hits.
        """
        if settings.cache_knowledge_context and lang in self._language_contexts:
            return self._language_contexts[lang]

        # 1. Documents directly in the requested language
        lang_docs = [d for d in self.manifest.documents if d.enabled and d.lang == lang]
        replaced_sources = {d.same_as for d in lang_docs if d.same_as}

        # 2. English fallback docs for topics not translated into this language
        fallback_docs = []
        if lang != "en":
            for d in self.manifest.documents:
                if d.enabled and d.lang == "en" and d.source not in replaced_sources:
                    fallback_docs.append(d)

        selected_docs = lang_docs + fallback_docs if lang != "en" else lang_docs

        context_parts = []
        for doc_meta in selected_docs:
            if doc_meta.id in self.documents_content:
                context_parts.append(
                    f"--- DOCUMENT: {doc_meta.title} (ID: {doc_meta.id}, Lang: {doc_meta.lang}) ---\n"
                    f"{self.documents_content[doc_meta.id].strip()}\n"
                )

        context = "\n".join(context_parts)
        self._language_contexts[lang] = context
        return context

    def to_status_response(self, is_active: bool = True) -> SnapshotStatusResponse:
        total_chars = sum(len(c) for c in self.documents_content.values())
        langs = list(set(d.lang for d in self.manifest.documents))
        return SnapshotStatusResponse(
            version=self.version,
            created_at=self.created_at,
            document_count=len(self.documents_content),
            total_characters=total_chars,
            languages=langs,
            documents=self.manifest.documents,
            is_active=is_active
        )


class SnapshotManager:
    def __init__(self):
        self.active_snapshot: Optional[KnowledgeSnapshot] = None
        self.storage = LocalStorageAdapter(base_dir=settings.data_dir)

    def load_and_validate_manifest(self) -> ManifestSchema:
        manifest_file = Path(settings.manifest_path)
        if not manifest_file.exists():
            raise ManifestValidationError(f"Manifest file not found at: {settings.manifest_path}")

        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            manifest = ManifestSchema(**data)
        except Exception as e:
            raise ManifestValidationError(f"Invalid manifest JSON schema: {e}")

        # Path traversal and safety checks
        for doc in manifest.documents:
            if ".." in doc.source or doc.source.startswith("/"):
                raise ManifestValidationError(f"Path traversal or absolute path detected in document source: {doc.source}")

            # Ensure it is not in do_not_ingest
            for blocked in manifest.do_not_ingest:
                if blocked in doc.source:
                    raise ManifestValidationError(f"Document {doc.source} matches do_not_ingest exclusion rule: {blocked}")

        return manifest

    def create_snapshot(self) -> KnowledgeSnapshot:
        manifest = self.load_and_validate_manifest()
        docs_content = {}
        all_chunks = []

        data_path = Path(settings.data_dir)

        for doc in manifest.documents:
            if not doc.enabled:
                continue

            file_path = data_path / doc.source
            if not file_path.exists():
                raise KnowledgeSnapshotError(f"Approved document not found on disk: {file_path}")

            try:
                content = strip_frontmatter(file_path.read_text(encoding="utf-8"))
                docs_content[doc.id] = content
                doc.char_count = len(content)

                # Chunk document
                chunks = chunk_document(
                    doc_id=doc.id,
                    title=doc.title,
                    content=content,
                    chunk_size=settings.rag_chunk_size,
                    overlap=settings.rag_chunk_overlap
                )
                all_chunks.extend(chunks)
            except Exception as e:
                raise KnowledgeSnapshotError(f"Failed to read/process document {doc.id}: {e}")

        version = f"v_{datetime.datetime.now(datetime.UTC).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        created_at = datetime.datetime.now(datetime.UTC).isoformat()

        snapshot = KnowledgeSnapshot(
            version=version,
            created_at=created_at,
            manifest=manifest,
            documents_content=docs_content,
            chunks=all_chunks
        )
        return snapshot

    def refresh(self) -> KnowledgeSnapshot:
        """Atomic snapshot reload with safe fallback."""
        logger.info("Initiating atomic knowledge snapshot refresh...")
        try:
            new_snapshot = self.create_snapshot()
            # Atomically swap active snapshot
            self.active_snapshot = new_snapshot
            logger.info(f"Knowledge snapshot activated successfully: {new_snapshot.version} ({len(new_snapshot.documents_content)} docs)")
            return new_snapshot
        except Exception as e:
            logger.error(f"Knowledge snapshot refresh failed: {e}. Preserving previous snapshot.")
            if not self.active_snapshot:
                raise
            return self.active_snapshot


snapshot_manager = SnapshotManager()

