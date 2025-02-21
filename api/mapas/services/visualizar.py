import folium
from folium.plugins import Fullscreen


def criar_mapa_interativo(origem, destino, coordenadas_rota, distancia_km, origem_info, destino_info):
    # Validar entradas
    if not all([origem, destino, coordenadas_rota]):
        raise ValueError("Coordenadas insuficientes para criar o mapa")

    # Calcular ponto médio para centralização do mapa
    mid_point = [
        (origem[0] + destino[0]) / 2,
        (origem[1] + destino[1]) / 2
    ]

    # Criar mapa com zoom adequado
    mapa = folium.Map(location=mid_point, zoom_start=13)

    # Adicionar rota detalhada
    folium.PolyLine(
        locations=coordenadas_rota,
        color='#1E90FF',
        weight=6,
        opacity=0.8,
        tooltip=f"Distância total: {distancia_km:.2f} km"
    ).add_to(mapa)

    # Adicionar marcadores com popups aprimorados
    folium.Marker(
        location=origem,
        popup=folium.Popup(
            f"<b>📍 Origem</b><br>"
            f"Rua: {origem_info['nome_rua']}<br>"
            f"Bairro: {origem_info['bairro']}",
            max_width=250
        ),
        icon=folium.Icon(color="green", icon="circle-play", prefix="fa")
    ).add_to(mapa)

    folium.Marker(
        location=destino,
        popup=folium.Popup(
            f"<b>🏁 Destino</b><br>"
            f"Rua: {destino_info['nome_rua']}<br>"
            f"Bairro: {destino_info['bairro']}",
            max_width=250
        ),
        icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa")
    ).add_to(mapa)

    # Adicionar controle de tela cheia
    Fullscreen().add_to(mapa)

    # Em vez de salvar o arquivo, renderizar e retornar o HTML como string
    html_conteudo = mapa.get_root().render()
    return html_conteudo
