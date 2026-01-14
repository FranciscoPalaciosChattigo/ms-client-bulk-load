#!/usr/bin/env python3
"""
Script para generar archivos CSV de prueba y probar el microservicio
"""
import csv
import requests
import time


def create_test_csv(filename: str = "test_data.csv", num_rows: int = 10000):
    """
    Crear un archivo CSV de prueba
    """
    print(f"📝 Creando archivo {filename} con {num_rows} filas...")
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Headers
        writer.writerow(['id', 'nombre', 'apellido', 'email', 'edad', 'ciudad', 'pais', 'telefono'])
        
        # Datos
        ciudades = ['Madrid', 'Barcelona', 'Valencia', 'Sevilla', 'Bilbao', 
                   'Málaga', 'Murcia', 'Alicante', 'Zaragoza', 'Córdoba']
        paises = ['España', 'México', 'Argentina', 'Colombia', 'Chile']
        
        for i in range(1, num_rows + 1):
            writer.writerow([
                f'ID{i:06d}',
                f'Nombre{i}',
                f'Apellido{i}',
                f'usuario{i}@example.com',
                20 + (i % 60),
                ciudades[i % len(ciudades)],
                paises[i % len(paises)],
                f'+34-{600000000 + i}'
            ])
    
    print(f"✅ Archivo {filename} creado exitosamente")
    return filename


def test_upload(csv_file: str, client_id: str = "TEST_CLIENT", file_id: str = None):
    """
    Probar el endpoint de carga
    """
    if file_id is None:
        file_id = f"TEST_FILE_{int(time.time())}"
    
    url = "http://localhost:8000/api/v1/upload"
    
    print(f"\n🚀 Enviando archivo a {url}")
    print(f"   Client ID: {client_id}")
    print(f"   File ID: {file_id}")
    
    with open(csv_file, 'rb') as f:
        files = {'file': (csv_file, f, 'text/csv')}
        data = {
            'client_id': client_id,
            'file_id': file_id
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(url, files=files, data=data)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ Carga exitosa!")
                print(f"   Documentos insertados: {result['documents_inserted']}")
                print(f"   Colección: {result['collection_name']}")
                print(f"   Tiempo de procesamiento: {result['processing_time_seconds']}s")
                print(f"   Tiempo total (incluye red): {elapsed_time:.2f}s")
                return result
            else:
                print(f"\n❌ Error: {response.status_code}")
                print(f"   Detalle: {response.json()}")
                return None
                
        except requests.exceptions.ConnectionError:
            print("\n❌ No se pudo conectar al servidor. ¿Está corriendo el microservicio?")
            print("   Ejecuta: uvicorn app.main:app --reload")
            return None
        except Exception as e:
            print(f"\n❌ Error inesperado: {e}")
            return None


def test_status(client_id: str, file_id: str):
    """
    Consultar el estado de una colección
    """
    url = f"http://localhost:8000/api/v1/status/{client_id}/{file_id}"
    
    print(f"\n🔍 Consultando estado...")
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            result = response.json()
            if result['exists']:
                print(f"✅ Colección encontrada")
                print(f"   Nombre: {result['collection_name']}")
                print(f"   Documentos: {result['document_count']}")
            else:
                print(f"❌ Colección no encontrada")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_health():
    """
    Verificar el health check
    """
    url = "http://localhost:8000/api/v1/health"
    
    print(f"\n💓 Health check...")
    
    try:
        response = requests.get(url)
        result = response.json()
        
        if result['status'] == 'healthy':
            print(f"✅ Servicio saludable")
            print(f"   MongoDB: {result['mongodb']}")
        else:
            print(f"⚠️  Servicio con problemas")
            print(f"   Estado: {result['status']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """
    Función principal
    """
    print("=" * 60)
    print("🧪 TEST SUITE - MS-Client-Bulk-Load")
    print("=" * 60)
    
    # 1. Health check
    test_health()
    
    # 2. Crear archivo de prueba
    print("\n" + "=" * 60)
    csv_file = create_test_csv("test_data.csv", num_rows=5000)
    
    # 3. Probar carga
    print("=" * 60)
    result = test_upload(csv_file)
    
    # 4. Consultar estado
    if result:
        print("=" * 60)
        test_status(result['client_id'], result['file_id'])
    
    print("\n" + "=" * 60)
    print("✅ Tests completados")
    print("=" * 60)


if __name__ == "__main__":
    main()
