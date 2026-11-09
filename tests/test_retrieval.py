"""Tests for Policy Chunking, BM25, Vector Embeddings, RRF, and Hybrid Retrieval."""

from pathlib import Path

from src.policy.chunker import PolicyChunker
from src.policy.loader import load_and_index_policies, load_policies_from_dir
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.embeddings import FastClinicalEmbedder
from src.retrieval.rrf import reciprocal_rank_fusion


def test_chunker_metadata():
    policies_dir = Path("data/policies")
    policies = load_policies_from_dir(policies_dir)
    assert len(policies) >= 8

    chunker = PolicyChunker(max_chunk_chars=500)
    lumbar_policy = next(p for p in policies if "LUMBAR" in p.id)
    chunks = chunker.chunk_policy(lumbar_policy)

    assert len(chunks) >= 2
    for c in chunks:
        assert c.policy_id == lumbar_policy.id
        assert c.procedure_name == lumbar_policy.procedure_name
        assert "72148" in c.cpt_codes


def test_bm25_exact_code_matching():
    bm25 = BM25Retriever()
    doc_ids = ["doc_lumbar", "doc_knee", "doc_glp1"]
    texts = [
        "Lumbar Spine MRI CPT 72148 for radiculopathy",
        "Knee arthroscopy CPT 29881 partial meniscectomy",
        "Semaglutide Ozempic HCPCS J3490 for diabetes mellitus",
    ]
    bm25.fit(doc_ids, texts)

    scores_72148 = bm25.score("72148")
    assert scores_72148[0][0] == "doc_lumbar"
    assert scores_72148[0][1] > 0.0

    scores_29881 = bm25.score("29881")
    assert scores_29881[0][0] == "doc_knee"


def test_dense_vector_semantic_matching():
    embedder = FastClinicalEmbedder()
    texts = [
        "Spine magnetic resonance imaging for lower back pain radiating down leg",
        "Outpatient surgical procedure for torn meniscus in the knee joint",
        "Injectable GLP-1 receptor agonist medication for glycemic control",
    ]
    vecs = embedder.embed_texts(texts)
    assert vecs.shape == (3, 384)

    query_vec = embedder.embed_query("knee meniscal tear surgery")
    from src.retrieval.embeddings import cosine_similarity
    sims = cosine_similarity(query_vec, vecs)
    best_idx = int(sims.argmax())
    assert best_idx == 1, f"Expected knee match (idx 1), got {best_idx}"


def test_rrf_combination():
    list1 = [("doc_a", 10.0), ("doc_b", 8.0), ("doc_c", 6.0)]
    list2 = [("doc_b", 50.0), ("doc_a", 40.0), ("doc_d", 30.0)]
    merged = reciprocal_rank_fusion([list1, list2], k=60)

    # doc_a and doc_b appear in top 2 of both, so they should lead
    top_docs = [item[0] for item in merged[:2]]
    assert "doc_a" in top_docs
    assert "doc_b" in top_docs


def test_hybrid_policy_retrieval_all_procedures():
    retriever, policies, chunks = load_and_index_policies(Path("data/policies"))

    test_queries = [
        ("72148", "POL-CMS-L34220-LUMBAR-MRI"),
        ("lumbar spine MRI without contrast", "POL-CMS-L34220-LUMBAR-MRI"),
        ("29881", "POL-COMM-CG-SURG-05-KNEE-ARTHRO"),
        ("knee arthroscopy meniscectomy", "POL-COMM-CG-SURG-05-KNEE-ARTHRO"),
        ("J3490", "POL-UHC-GLP1-DIABETES"),
        ("Semaglutide Ozempic diabetes", "POL-UHC-GLP1-DIABETES"),
        ("95810", "POL-CMS-L36593-SLEEP-STUDY"),
        ("in-lab polysomnography sleep apnea", "POL-CMS-L36593-SLEEP-STUDY"),
        ("J0135", "POL-AETNA-CPB0315-BIOLOGICS-RA"),
        ("Adalimumab Humira for rheumatoid arthritis", "POL-AETNA-CPB0315-BIOLOGICS-RA"),
        ("43644", "POL-CMS-NCD100.1-BARIATRIC"),
        ("Roux-en-Y gastric bypass bariatric surgery", "POL-CMS-NCD100.1-BARIATRIC"),
        ("E0601", "POL-CMS-L33718-CPAP"),
        ("continuous positive airway pressure cpap", "POL-CMS-L33718-CPAP"),
        ("97110", "POL-CMS-L35036-PT-EXTENSION"),
        ("physical therapy extension skilled care", "POL-CMS-L35036-PT-EXTENSION"),
    ]

    for query, expected_policy_id in test_queries:
        results = retriever.retrieve(query, top_k=3, use_hybrid=True)
        assert len(results) > 0
        top_policy_id = results[0].policy_id
        assert top_policy_id == expected_policy_id, (
            f"Query '{query}' expected '{expected_policy_id}' but got '{top_policy_id}'"
        )

