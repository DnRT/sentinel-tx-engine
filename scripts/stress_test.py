import asyncio
import aiohttp
import time
import statistics

# Configuraciones
URL = "http://localhost:8000/api/v1/validar_pago"
PAYLOAD = {
  "usuario_id": 1,
  "monto": 500,
  "cuenta_destino": "UNI-999888",
  "ip_origen": "190.160.10.20",
  "hardware_id": "MAC-12-34-56-78"
}

async def fetch(session, url):
    try:
        async with session.post(url, json=PAYLOAD) as response:
            return response.status
    except Exception as e:
        return 500

async def run_stress_test(total_requests, concurrency):
    print(f"\n--- INICIANDO PRUEBA: {total_requests} transacciones (Concurrencia: {concurrency}) ---")
    start_time = time.time()
    
    connector = aiohttp.TCPConnector(limit=concurrency)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for _ in range(total_requests):
            tasks.append(fetch(session, URL))
        
        responses = await asyncio.gather(*tasks)
        
    end_time = time.time()
    
    success = responses.count(200)
    failed = len(responses) - success
    elapsed_time = end_time - start_time
    req_per_sec = total_requests / elapsed_time if elapsed_time > 0 else 0
    
    print(f"Tiempo Total: {elapsed_time:.2f} segundos")
    print(f"Transacciones / Segundo (RPS): {req_per_sec:.2f}")
    print(f"Exitosas: {success} | Fallidas: {failed}")
    
    return req_per_sec

async def main():
    # Prueba 1: 1,000 transacciones
    res_1k = await run_stress_test(total_requests=1000, concurrency=10)
    
    # Prueba 2: 5,000 transacciones
    res_5k = await run_stress_test(total_requests=5000, concurrency=20)
    
    # Prueba 3: 10,000 transacciones
    res_10k = await run_stress_test(total_requests=10000, concurrency=30)
    
    print("\n=== RESUMEN PARA LA TABLA DEL README ===")
    print(f"1k: {res_1k:.2f} RPS")
    print(f"5k: {res_5k:.2f} RPS")
    print(f"10k: {res_10k:.2f} RPS")

if __name__ == "__main__":
    asyncio.run(main())
