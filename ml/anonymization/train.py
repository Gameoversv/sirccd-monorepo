"""
train.py — Entrenamiento de YOLO11s para anonimización (rostros + placas)

Uso local:
  python ml/anonymization/train.py

Uso en Colab:
  from ml.anonymization.train import train
  train(data="/content/anonymization/data.yaml",
        project="/content/drive/MyDrive/sirccd/anonymization/runs")
"""

from pathlib import Path
from ultralytics import YOLO


def train(
    model_name: str = "yolo11s.pt",
    data: str | None = None,
    epochs: int = 150,
    imgsz: int = 640,
    batch: int = 16,
    project: str | None = None,
    name: str = "anonymizer_v1",
    resume: bool = False,
):
    """
    Entrena YOLO11s para detección de rostros y placas.

    Args:
        model_name: Pesos base (yolo11s.pt, yolo11m.pt, o ruta a last.pt para resume)
        data: Ruta al data.yaml. Si None, usa el default del proyecto.
        epochs: Número de épocas.
        imgsz: Tamaño de imagen de entrada.
        batch: Tamaño de batch (reducir si OOM).
        project: Directorio de salida para runs.
        name: Nombre del experimento.
        resume: Si True, resume desde el último checkpoint.
    """
    base = Path(__file__).resolve().parent

    if data is None:
        data = str(base / "data.yaml")

    if project is None:
        project = str(base / "runs")

    # Cargar modelo
    if resume:
        # Resumir desde último checkpoint
        last_pt = Path(project) / name / "weights" / "last.pt"
        if last_pt.exists():
            model = YOLO(str(last_pt))
            print(f"Resumiendo desde: {last_pt}")
        else:
            print(f"No se encontró {last_pt}, iniciando desde {model_name}")
            model = YOLO(model_name)
    else:
        model = YOLO(model_name)

    print(f"Modelo: {model_name}")
    print(f"Dataset: {data}")
    print(f"Épocas: {epochs}, ImgSz: {imgsz}, Batch: {batch}")
    print(f"Proyecto: {project}/{name}")
    print("=" * 60)

    results = model.train(
        data=data,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        project=project,
        name=name,
        exist_ok=True,

        # Optimizer
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        weight_decay=0.0005,
        warmup_epochs=5,
        cos_lr=True,

        # Early stopping
        patience=30,

        # Augmentations
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=5.0,
        translate=0.1,
        scale=0.5,
        shear=2.0,
        flipud=0.0,       # No voltear verticalmente
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
        copy_paste=0.1,

        # Logging
        plots=True,
        save=True,
        save_period=25,    # Guardar checkpoint cada 25 épocas
        verbose=True,
    )

    # Evaluar en test set
    print("\n" + "=" * 60)
    print("Evaluación en Test Set")
    print("=" * 60)

    best_pt = Path(project) / name / "weights" / "best.pt"
    if best_pt.exists():
        best_model = YOLO(str(best_pt))
        test_results = best_model.val(
            data=data,
            split="test",
            imgsz=imgsz,
            batch=batch,
            project=project,
            name=f"{name}_test",
            plots=True,
        )
        print(f"\nmAP@0.5:     {test_results.box.map50:.4f}")
        print(f"mAP@0.5:0.95: {test_results.box.map:.4f}")

    print(f"\n✅ Entrenamiento completado")
    print(f"   Best weights: {best_pt}")

    return results


if __name__ == "__main__":
    train()
