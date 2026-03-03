"""
Test del servicio de deduplicación B-07
Verifica embeddings visuales, FAISS index y lógica combinada
"""

import sys
from pathlib import Path
import numpy as np
from PIL import Image
import io

# Añadir backend al path
sys.path.insert(0, str(Path(__file__).parent))

from services.deduplication_service import (
    VisualEmbedder,
    FAISSIndex,
    haversine_distance
)


def test_visual_embedder():
    """Test del generador de embeddings"""
    print("\n" + "="*60)
    print("TEST 1: Visual Embedder")
    print("="*60)
    
    try:
        embedder = VisualEmbedder(model_name="resnet50")
        print(f"✓ Modelo cargado: ResNet50")
        print(f"✓ Dimensión de embeddings: {embedder.embedding_dim}")
        print(f"✓ Dispositivo: {embedder.device}")
        
        # Crear imagen de prueba (ruido aleatorio)
        img_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        
        # Generar embedding
        embedding = embedder.embed(img)
        
        print(f"✓ Embedding generado: shape={embedding.shape}")
        print(f"✓ Rango de valores: [{embedding.min():.4f}, {embedding.max():.4f}]")
        
        # Verificar normalización L2
        norm = np.linalg.norm(embedding)
        print(f"✓ Norma L2: {norm:.6f} (debe estar ~1.0)")
        
        assert embedding.shape == (embedder.embedding_dim,), "Dimensión incorrecta"
        assert abs(norm - 1.0) < 1e-4, "Embedding no normalizado"
        
        print("\n✅ TEST 1 PASADO: VisualEmbedder funciona correctamente")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 1 FALLIDO: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_faiss_index():
    """Test del índice FAISS"""
    print("\n" + "="*60)
    print("TEST 2: FAISS Index")
    print("="*60)
    
    try:
        embedding_dim = 128
        index = FAISSIndex(embedding_dim=embedding_dim, index_type="L2")
        print(f"✓ Índice FAISS creado: dim={embedding_dim}, tipo=L2")
        
        # Crear embeddings de prueba
        n_samples = 100
        embeddings = np.random.randn(n_samples, embedding_dim).astype('float32')
        
        # Normalizar L2
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms
        
        report_ids = list(range(1, n_samples + 1))
        
        # Añadir al índice
        index.add(embeddings, report_ids)
        print(f"✓ Añadidos {n_samples} embeddings al índice")
        print(f"✓ Total en índice: {index.index.ntotal}")
        
        # Buscar vecino más cercano del primer embedding (debe ser él mismo)
        query = embeddings[0].reshape(1, -1)
        distances, ids = index.search(query, k=3)
        
        print(f"✓ Búsqueda k=3 completada")
        print(f"  - IDs encontrados: {ids}")
        print(f"  - Distancias: {distances}")
        
        assert ids[0] == 1, f"El primer resultado debe ser ID=1, obtenido: {ids[0]}"
        assert distances[0] < 1e-5, f"Distancia debe ser ~0, obtenida: {distances[0]}"
        
        # Test de persistencia
        test_path = "./test_index.bin"
        index.save(test_path)
        print(f"✓ Índice guardado en {test_path}")
        
        # Cargar índice
        index2 = FAISSIndex(embedding_dim=embedding_dim)
        index2.load(test_path)
        print(f"✓ Índice cargado desde {test_path}")
        print(f"  - Total cargado: {index2.index.ntotal}")
        
        assert index2.index.ntotal == n_samples, "Tamaño del índice no coincide"
        
        # Limpiar archivos de prueba
        Path(test_path).unlink()
        Path(test_path + ".ids").unlink()
        
        print("\n✅ TEST 2 PASADO: FAISS Index funciona correctamente")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 2 FALLIDO: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_haversine_distance():
    """Test del cálculo de distancia geográfica"""
    print("\n" + "="*60)
    print("TEST 3: Haversine Distance")
    print("="*60)
    
    try:
        # Santiago de los Caballeros, RD (aproximado)
        lat1, lon1 = 19.4515, -70.6974
        
        # Casos de prueba
        test_cases = [
            # Mismo punto
            {
                "name": "Mismo punto",
                "lat2": lat1,
                "lon2": lon1,
                "expected": 0.0,
                "tolerance": 1.0
            },
            # ~100m al norte
            {
                "name": "~100m al norte",
                "lat2": lat1 + 0.0009,  # ~100m
                "lon2": lon1,
                "expected": 100.0,
                "tolerance": 10.0
            },
            # ~1km al este
            {
                "name": "~1km al este",
                "lat2": lat1,
                "lon2": lon1 + 0.009,  # ~1km
                "expected": 1000.0,
                "tolerance": 100.0
            }
        ]
        
        for case in test_cases:
            distance = haversine_distance(lat1, lon1, case["lat2"], case["lon2"])
            error = abs(distance - case["expected"])
            
            print(f"\n{case['name']}:")
            print(f"  - Distancia calculada: {distance:.2f} m")
            print(f"  - Distancia esperada: {case['expected']:.2f} m")
            print(f"  - Error: {error:.2f} m")
            
            assert error < case["tolerance"], f"Error excede tolerancia: {error} > {case['tolerance']}"
            print(f"  ✓ OK (dentro de tolerancia)")
        
        print("\n✅ TEST 3 PASADO: Haversine funciona correctamente")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 3 FALLIDO: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_embedder_similarity():
    """Test de similitud entre imágenes idénticas y diferentes"""
    print("\n" + "="*60)
    print("TEST 4: Similitud de Embeddings")
    print("="*60)
    
    try:
        embedder = VisualEmbedder(model_name="resnet50")
        
        # Crear imagen base
        img_array1 = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        img1 = Image.fromarray(img_array1)
        
        # Imagen idéntica
        img2 = img1.copy()
        
        # Imagen diferente
        img_array3 = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        img3 = Image.fromarray(img_array3)
        
        # Generar embeddings
        emb1 = embedder.embed(img1)
        emb2 = embedder.embed(img2)
        emb3 = embedder.embed(img3)
        
        # Distancias L2
        dist_identical = np.linalg.norm(emb1 - emb2)
        dist_different = np.linalg.norm(emb1 - emb3)
        
        print(f"Distancia L2 (imágenes idénticas): {dist_identical:.6f}")
        print(f"Distancia L2 (imágenes diferentes): {dist_different:.6f}")
        
        assert dist_identical < 1e-5, "Imágenes idénticas deben tener distancia ~0"
        assert dist_different > 0.1, "Imágenes diferentes deben tener distancia > 0.1"
        
        print("\n✅ TEST 4 PASADO: Similitud funciona como esperado")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 4 FALLIDO: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecutar todos los tests"""
    print("\n" + "="*60)
    print("TESTS DEL SERVICIO DE DEDUPLICACIÓN B-07")
    print("="*60)
    
    results = []
    
    # Ejecutar tests
    results.append(("Visual Embedder", test_visual_embedder()))
    results.append(("FAISS Index", test_faiss_index()))
    results.append(("Haversine Distance", test_haversine_distance()))
    results.append(("Similitud de Embeddings", test_embedder_similarity()))
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE TESTS")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASADO" if result else "❌ FALLIDO"
        print(f"{name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests pasados")
    
    if passed == total:
        print("\n🎉 TODOS LOS TESTS PASADOS 🎉")
        return 0
    else:
        print(f"\n⚠️ {total - passed} TEST(S) FALLIDO(S)")
        return 1


if __name__ == "__main__":
    exit(main())
