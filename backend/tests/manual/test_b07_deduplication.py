"""
Tests del servicio de deduplicacion B-07/M-11.

Valida:
- Generacion de embeddings
- Operaciones basicas de FAISS
- Distancia geografica Haversine
- Separacion de similitud entre imagenes identicas y distintas
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np  # type: ignore
from PIL import Image  # type: ignore

# Anadir backend al path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from services.deduplication_service import FAISSIndex, VisualEmbedder, haversine_distance


def test_visual_embedder() -> None:
    print("\n" + "=" * 60)
    print("TEST 1: Visual Embedder")
    print("=" * 60)

    try:
        embedder = VisualEmbedder(model_name="resnet50")
        print(f"Modelo solicitado: resnet50")
        print(f"Backend efectivo: {embedder.backend}")
        print(f"Dimension embedding: {embedder.embedding_dim}")
        print(f"Dispositivo: {embedder.device}")

        img_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)

        embedding = embedder.embed(img)
        norm = np.linalg.norm(embedding)

        print(f"Embedding generado: shape={embedding.shape}")
        print(f"Norma L2: {norm:.6f}")

        assert embedding.shape == (embedder.embedding_dim,), "Dimension incorrecta"
        assert abs(norm - 1.0) < 1e-4, "Embedding no normalizado"

        print("\nTEST 1 PASADO")
    except Exception as exc:
        print(f"\nTEST 1 FALLIDO: {exc}")
        import traceback

        traceback.print_exc()
        raise


def test_faiss_index() -> None:
    print("\n" + "=" * 60)
    print("TEST 2: FAISS Index")
    print("=" * 60)

    try:
        embedding_dim = 128
        index = FAISSIndex(embedding_dim=embedding_dim, index_type="L2")

        n_samples = 100
        embeddings = np.random.randn(n_samples, embedding_dim).astype("float32")
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / np.maximum(norms, 1e-9)

        report_ids = list(range(1, n_samples + 1))
        index.add(embeddings, report_ids)

        query = embeddings[0]
        distances, ids = index.search(query, k=3)

        print(f"IDs encontrados: {ids}")
        print(f"Distancias: {distances.tolist() if len(distances) else []}")

        assert ids[0] == 1, "El primer vecino debe ser el mismo vector"
        assert distances[0] < 1e-5, "Distancia esperada ~0 para vector identico"

        test_path = "./test_index.faiss"
        index.save(test_path)

        loaded = FAISSIndex(embedding_dim=embedding_dim, index_type="L2")
        loaded.load(test_path)

        assert loaded.index.ntotal == n_samples, "Tamano de indice no coincide"

        Path(test_path).unlink(missing_ok=True)
        Path(test_path + ".ids").unlink(missing_ok=True)

        print("\nTEST 2 PASADO")
    except Exception as exc:
        print(f"\nTEST 2 FALLIDO: {exc}")
        import traceback

        traceback.print_exc()
        raise


def test_haversine_distance() -> None:
    print("\n" + "=" * 60)
    print("TEST 3: Haversine Distance")
    print("=" * 60)

    try:
        lat1, lon1 = 19.4515, -70.6974

        d_same = haversine_distance(lat1, lon1, lat1, lon1)
        d_100m = haversine_distance(lat1, lon1, lat1 + 0.0009, lon1)
        d_1km = haversine_distance(lat1, lon1, lat1, lon1 + 0.009)

        print(f"Mismo punto: {d_same:.3f} m")
        print(f"Aprox 100m: {d_100m:.3f} m")
        print(f"Aprox 1km: {d_1km:.3f} m")

        assert d_same < 1.0, "Distancia en mismo punto debe ser ~0"
        assert 90 < d_100m < 110, "Distancia de 100m fuera de rango esperado"
        assert 900 < d_1km < 1100, "Distancia de 1km fuera de rango esperado"

        print("\nTEST 3 PASADO")
    except Exception as exc:
        print(f"\nTEST 3 FALLIDO: {exc}")
        import traceback

        traceback.print_exc()
        raise


def test_embedder_similarity() -> None:
    print("\n" + "=" * 60)
    print("TEST 4: Similitud de Embeddings")
    print("=" * 60)

    try:
        embedder = VisualEmbedder(model_name="resnet50")

        rng = np.random.default_rng(42)
        img_array1 = rng.integers(0, 255, (224, 224, 3), dtype=np.uint8)
        img_array2 = img_array1.copy()
        img_array3 = rng.integers(0, 255, (224, 224, 3), dtype=np.uint8)

        img1 = Image.fromarray(img_array1)
        img2 = Image.fromarray(img_array2)
        img3 = Image.fromarray(img_array3)

        emb1 = embedder.embed(img1)
        emb2 = embedder.embed(img2)
        emb3 = embedder.embed(img3)

        dist_identical = np.linalg.norm(emb1 - emb2)
        dist_different = np.linalg.norm(emb1 - emb3)

        print(f"Distancia (identicas): {dist_identical:.6f}")
        print(f"Distancia (distintas): {dist_different:.6f}")

        assert dist_identical < 1e-5, "Imagenes identicas deben tener distancia ~0"
        assert dist_different > 1e-3, "Imagenes distintas deben tener distancia > 0"

        print("\nTEST 4 PASADO")
    except Exception as exc:
        print(f"\nTEST 4 FALLIDO: {exc}")
        import traceback

        traceback.print_exc()
        raise


def main() -> int:
    print("\n" + "=" * 60)
    print("TESTS DEL SERVICIO DE DEDUPLICACION B-07/M-11")
    print("=" * 60)

    cases = [
        ("Visual Embedder", test_visual_embedder),
        ("FAISS Index", test_faiss_index),
        ("Haversine Distance", test_haversine_distance),
        ("Similitud de Embeddings", test_embedder_similarity),
    ]

    results = []
    for name, fn in cases:
        try:
            fn()
            results.append((name, True))
        except Exception:
            results.append((name, False))

    print("\n" + "=" * 60)
    print("RESUMEN DE TESTS")
    print("=" * 60)

    passed = sum(1 for _, ok in results if ok)
    total = len(results)

    for name, ok in results:
        print(f"{name}: {'PASADO' if ok else 'FALLIDO'}")

    print(f"\nTotal: {passed}/{total} tests pasados")

    if passed == total:
        print("\nTODOS LOS TESTS PASADOS")
        return 0

    print("\nHAY TESTS FALLIDOS")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
