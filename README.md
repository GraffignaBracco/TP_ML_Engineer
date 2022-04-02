# TP_ML_Engineer

## Servicios Utilizados

1. S3: Acá se suben los archivos de kaggle.

2. Sagemaker Studio: Esta herramienta se utilizó para entrenar el modelo de Random Cut Forest y crear un endpoint para su posterior uso. Los pasos para utilzar la herramienta son:
    a. Crear un servicio de sagemaker studio.
    b. Leer los datos desde s3.
    c. Armar un dataset de entrenamiento.
    d. Entrenar un modelo Random Cut Forest
    e. Crear un endpoint con el modelo