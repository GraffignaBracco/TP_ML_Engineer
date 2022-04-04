# TP_ML_Engineer

## Servicios Utilizados

1. S3: Acá se suben los archivos de kaggle.

2. VPC: Se creó una VPC en us-east-2 para que los servicios puedan comunicarse entre si.

3. Sagemaker Studio: Esta herramienta se utilizó para entrenar el modelo de Random Cut Forest y crear un endpoint para su posterior uso. Los pasos para utilzar la herramienta son:

    * Crear un Sagemaker Studio 
    * Correr todas las funciones y pasos que están en el Notebook Sagemaker_Studio.ipynb que realliza los sigjuientes pasos
        * Leer los datos desde s3.
        * Armar un dataset de entrenamiento.
        * Entrenar un modelo Random Cut Forest
        * Crear un endpoint con el modelo

4. Managed workflows por Apache Airflow: Con este servicio se corren unas funciones una vez por año. Las Funciones son:
    * get_latest_year_file: Lee los archivos que están en la carpeta "tp" del bucket "tpmlengineer" y obtiene el año del archivo más reciente.
    * download_file: Baja el archivo desde s3 y lo guarda en un dataframe de pandas con solamente las columnas que se utilizan posteriormente.
    * transform_file: Agrupa el dataframe por aeropuerto y día y calcula la cantidad de vuelos y el promedio de demora por día y por aeropuerto.
    * predict_anomalies: Hace un request al endpoint del modelo desarrollado en Sagemaker studio con las demoras promedio por día y por aeropuerto. El resultado del endpoint es un score. Una vez que están los scores calculados para todo el dataframe, se cacula el score promedio y su desviación estandar. Si el score para un día y aeropuerto particular, es superior a la media más 3 veces el desvío estandar entonces se considera que las demoras no fueron normales.
    * graph_airport: Esta función crea un gráfico para cada aeropuerto con la cantidad de vuelos que tuvieron por día y con un punto rojo aquellos días que fueron considerados anómalos. Todos los gráficos son guardados en una carpeta por año dentro del bucket. En este repositorio hay una muestra en la carpeta "imagenes" con todos los gráficos generados por aeropuerto para los años 2017 y 2018.

    ![alt text](https://github.com/GraffignaBracco/TP_ML_Engineer/blob/main/imagenes/2018/ACT.png?raw=true)
    * upload_to_database: Sube el dataframe con la información de las cantidad de vuelos, demoras promedio y si son consideradas anómalas por día y aeropuerto a una base de datos Postgres en RDS.


5. Amazon RDS (Postgres): Este servicio se crea para guardar los datos generados por el proceso de Airflow.

## Arquitectura

![alt text](https://github.com/GraffignaBracco/TP_ML_Engineer/blob/main/Cloud_Architecture_TP_ML_Engineer.drawio.pdf)