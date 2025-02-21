import requests
import random
import urllib.parse
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuração da API e quantidade de corridas
API_URL = "http://127.0.0.1:8000"
NUM_CORRIDAS = 2000
CITY = "Vitória da Conquista"


def obter_clientes():
    """Obtém a lista de clientes da API."""
    url = f"{API_URL}/clientes/listar/"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Se a resposta indicar que não há clientes, retorna lista vazia.
            if isinstance(data, dict) and data.get("mensagem"):
                return []
            return data
        else:
            print(f"Erro ao buscar clientes: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Exceção ao buscar clientes: {e}")
        return []


def obter_coordenadas_aleatorias():
    """Obtém coordenadas de origem e destino aleatórias da API."""
    # Codifica a cidade para ser usada na URL (para tratar espaços etc.)
    city_encoded = urllib.parse.quote(CITY)
    url = f"{API_URL}/mapas/selecionar_coordenadas_aleatorias?cidade={city_encoded}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro ao buscar coordenadas: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exceção ao buscar coordenadas: {e}")
        return None


def gerar_horario_pedido():
    """
    Gera um horário aleatório para o dia 2024-06-01, distribuindo os 86.400 segundos do dia.
    """
    base_date = datetime(2024, 6, 1)
    seconds = random.randint(0, 86399)  # 0 a 86399 segundos
    pedido_time = base_date + timedelta(seconds=seconds)
    return pedido_time.isoformat()


def solicitar_corrida(id_cliente):
    """Solicita uma corrida para um cliente específico."""
    coordenadas = obter_coordenadas_aleatorias()
    if not coordenadas:
        print(f"❌ Não foi possível obter coordenadas para o cliente {id_cliente}")
        return

    origem = coordenadas.get("origem")
    destino = coordenadas.get("destino")
    if not origem or not destino:
        print(f"❌ Dados incompletos de coordenadas para o cliente {id_cliente}")
        return

    corrida_data = {
        "cliente": {"id_cliente": id_cliente},
        "origem": {
            "latitude": origem["latitude"],
            "longitude": origem["longitude"],
            "nome_rua": origem["nome_rua"],
            "bairro": origem["bairro"]
        },
        "destino": {
            "latitude": destino["latitude"],
            "longitude": destino["longitude"],
            "nome_rua": destino["nome_rua"],
            "bairro": destino["bairro"]
        },
        "horario_pedido": gerar_horario_pedido()
    }

    url = f"{API_URL}/corridas/solicitar"
    try:
        response = requests.post(url, json=corrida_data)
        if response.status_code == 201:
            print(f"✔️ Corrida solicitada para o cliente {id_cliente}")
        else:
            try:
                error_detail = response.json()
            except Exception:
                error_detail = response.text
            print(f"❌ Erro ao solicitar corrida para o cliente {id_cliente}: {response.status_code} - {error_detail}")
    except Exception as e:
        print(f"Exceção ao solicitar corrida para o cliente {id_cliente}: {e}")


def simular_corridas():
    """Executa a simulação de 2.000 corridas distribuídas ao longo do dia."""
    clientes = obter_clientes()
    if not clientes:
        print("⚠️ Nenhum cliente encontrado. Simulação abortada.")
        return

    # Cria um pool de threads (limite de 100 threads concorrentes, por exemplo)
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = []
        for _ in range(NUM_CORRIDAS):
            cliente = random.choice(clientes)
            id_cliente = cliente.get("id")
            futures.append(executor.submit(solicitar_corrida, id_cliente))

        # Aguarda a conclusão de todas as tarefas (opcional)
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Erro na execução: {e}")


if __name__ == "__main__":
    simular_corridas()
