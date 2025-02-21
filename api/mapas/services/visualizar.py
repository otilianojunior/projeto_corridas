import folium
from folium.plugins import Fullscreen


def criar_mapa_interativo(origem, destino, coordenadas_rota, distancia_km, origem_info, destino_info):
    """
    Cria um mapa interativo com a rota entre origem e destino.

    Parâmetros:
    - origem: (latitude, longitude) da origem.
    - destino: (latitude, longitude) do destino.
    - coordenadas_rota: Lista de pontos da rota [(lat, lon), ...].
    - distancia_km: Distância total da rota em quilômetros.
    - origem_info: Dicionário com detalhes da origem (nome da rua, bairro).
    - destino_info: Dicionário com detalhes do destino (nome da rua, bairro).

    Retorna:
    - HTML renderizado do mapa interativo.
    """

    # Validação de entradas
    if not origem or not destino or not coordenadas_rota:
        raise ValueError("Coordenadas insuficientes para criar o mapa.")

    if not isinstance(coordenadas_rota, list) or len(coordenadas_rota) < 2:
        raise ValueError("A rota precisa de pelo menos dois pontos válidos.")

    # Calcular ponto médio para centralizar o mapa
    mid_point = [
        (origem[0] + destino[0]) / 2,
        (origem[1] + destino[1]) / 2
    ]

    # Criar o mapa interativo com zoom ajustável
    mapa = folium.Map(location=mid_point, zoom_start=14, control_scale=True)

    # Adicionar a rota ao mapa
    folium.PolyLine(
        locations=coordenadas_rota,
        color='#1E90FF',
        weight=6,
        opacity=0.8,
        tooltip=f"🛣️ Distância total: {distancia_km:.2f} km"
    ).add_to(mapa)

    # Criar marcadores detalhados
    folium.Marker(
        location=origem,
        popup=folium.Popup(
            f"<b>📍 Origem</b><br>"
            f"<b>Rua:</b> {origem_info.get('nome_rua', 'Desconhecido')}<br>"
            f"<b>Bairro:</b> {origem_info.get('bairro', 'Desconhecido')}",
            max_width=250
        ),
        icon=folium.Icon(color="green", icon="circle-play", prefix="fa")
    ).add_to(mapa)

    folium.Marker(
        location=destino,
        popup=folium.Popup(
            f"<b>🏁 Destino</b><br>"
            f"<b>Rua:</b> {destino_info.get('nome_rua', 'Desconhecido')}<br>"
            f"<b>Bairro:</b> {destino_info.get('bairro', 'Desconhecido')}",
            max_width=250
        ),
        icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa")
    ).add_to(mapa)

    # Adicionar controle de tela cheia ao mapa
    Fullscreen().add_to(mapa)

    # Renderizar e retornar o HTML do mapa como string
    return mapa.get_root().render()
