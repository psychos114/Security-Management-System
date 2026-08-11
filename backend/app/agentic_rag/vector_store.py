import json
from pathlib import Path

import faiss
import numpy as np


def get_index_files(base_path):
    """
    返回FAISS索引的三个文件路径。
    """
    base_path = Path(base_path)

    return {
        "index": Path(str(base_path) + ".index"),
        "metadata": Path(
            str(base_path) + ".metadata.json"
        ),
        "manifest": Path(
            str(base_path) + ".manifest.json"
        ),
    }


def create_index(embeddings):
    """
    创建余弦相似度FAISS索引。
    """
    if not embeddings:
        raise RuntimeError(
            "没有向量，无法创建索引"
        )

    vectors = np.asarray(
        embeddings,
        dtype=np.float32,
    )

    if vectors.ndim != 2:
        raise RuntimeError(
            "向量必须是二维数据"
        )

    faiss.normalize_L2(vectors)

    dimension = vectors.shape[1]

    index = faiss.IndexFlatIP(dimension)
    index.add(vectors)

    return index


def save_vector_store(
    base_path,
    index,
    metadata,
    manifest,
):
    """
    保存FAISS、资料映射和索引说明。
    """
    files = get_index_files(base_path)

    files["index"].parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if index.ntotal != len(metadata):
        raise RuntimeError(
            "FAISS向量数量与资料映射数量不一致"
        )

    serialized_index = faiss.serialize_index(
        index
    )

    files["index"].write_bytes(
        serialized_index.tobytes()
    )

    files["metadata"].write_text(
        json.dumps(
            {"items": metadata},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    files["manifest"].write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return files


def load_vector_store(base_path):
    """
    重新加载已经保存的FAISS索引。
    """
    files = get_index_files(base_path)

    for file_path in files.values():
        if not file_path.exists():
            raise FileNotFoundError(
                f"缺少索引文件：{file_path}"
            )

    raw_index = np.frombuffer(
        files["index"].read_bytes(),
        dtype=np.uint8,
    )

    index = faiss.deserialize_index(
        raw_index
    )

    metadata_payload = json.loads(
        files["metadata"].read_text(
            encoding="utf-8"
        )
    )

    manifest = json.loads(
        files["manifest"].read_text(
            encoding="utf-8"
        )
    )

    return {
        "index": index,
        "metadata": metadata_payload["items"],
        "manifest": manifest,
        "files": files,
    }