import folium
from folium.plugins import Fullscreen
from branca.element import Element

def criar_mapa_interativo(corrida, coordenadas_rota):
    # Verificação básica
    if not corrida.origem_latitude or not corrida.destino_latitude or not coordenadas_rota:
        raise ValueError("Coordenadas insuficientes para criar o mapa.")

    if not isinstance(coordenadas_rota, list) or len(coordenadas_rota) < 2:
        raise ValueError("A rota precisa de pelo menos dois pontos válidos.")

    origem = (corrida.origem_latitude, corrida.origem_longitude)
    destino = (corrida.destino_latitude, corrida.destino_longitude)

    mid_point = [
        (origem[0] + destino[0]) / 2,
        (origem[1] + destino[1]) / 2
    ]

    mapa = folium.Map(location=mid_point, zoom_start=14, control_scale=True)

    tooltip_text = f"Distância total: {corrida.distancia_km:.2f} km"
    if corrida.preco_total is not None:
        tooltip_text += f" | Preço total: R$ {corrida.preco_total:.2f}"

    folium.PolyLine(
        locations=coordenadas_rota,
        color='#1E90FF',
        weight=6,
        opacity=0.8,
        tooltip=tooltip_text
    ).add_to(mapa)

    # Marcar os nós da rota
    for ponto in coordenadas_rota:
        folium.CircleMarker(
            location=ponto,
            radius=1.5,
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=0.9
        ).add_to(mapa)

    # Marcador da origem
    folium.Marker(
        location=origem,
        popup=folium.Popup(
            f"<b>📍 Origem</b><br>"
            f"<b>Rua:</b> {corrida.origem_rua or 'Desconhecido'}<br>"
            f"<b>Bairro:</b> {corrida.origem_bairro or 'Desconhecido'}",
            max_width=250
        ),
        icon=folium.Icon(color="green", icon="circle-play", prefix="fa")
    ).add_to(mapa)

    # Marcador do destino
    folium.Marker(
        location=destino,
        popup=folium.Popup(
            f"<b>🏁 Destino</b><br>"
            f"<b>Rua:</b> {corrida.destino_rua or 'Desconhecido'}<br>"
            f"<b>Bairro:</b> {corrida.destino_bairro or 'Desconhecido'}",
            max_width=250
        ),
        icon=folium.Icon(color="gray", icon="flag-checkered", prefix="fa")
    ).add_to(mapa)

    Fullscreen().add_to(mapa)

    # Formata o horário de forma legível
    horario_formatado = corrida.horario_pedido.strftime("%H:%M") if corrida.horario_pedido else "Desconhecido"

    # Tela flutuante
    info_html = f"""
    <div style="
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        background-color: white;
        padding: 15px;
        border: 2px solid #1E90FF;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0,0,0,0.3);
        font-family: Arial, sans-serif;
        font-size: 14px;
        max-width: 300px;
    ">
        <b>Informações da Corrida</b><br>
        <b>Origem:</b> {corrida.origem_rua or 'Desconhecido'} - {corrida.origem_bairro or 'Desconhecido'}<br>
        <b>Destino:</b> {corrida.destino_rua or 'Desconhecido'} - {corrida.destino_bairro or 'Desconhecido'}<br>
        <b>Distância:</b> {corrida.distancia_km:.2f} km<br>
        <b>Preço:</b> R$ {corrida.preco_total:.2f} <br>
        <b>Horário do Pedido:</b> {horario_formatado}
    </div>
    """
    info_element = Element(info_html)
    mapa.get_root().html.add_child(info_element)

    return mapa.get_root().render()