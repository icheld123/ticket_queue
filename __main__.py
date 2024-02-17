"""Programa que simula una cola de cajero de manera gráfica usando Pygame."""

import sys, pygame, random, pandas
import logic, view, params

if __name__ == '__main__':
    pygame.init()

    # Declaración de variables de ejecución
    screen = pygame.display.set_mode((params.SCREEN_WIDTH, params.SCREEN_HEIGHT))
    pygame.display.set_caption('Venta de boletas')
    clock = pygame.time.Clock()
    time = 0

    # Declaración de los eventos para atención y si la ejecución es automática.
    MANUAL_RESPOND = pygame.USEREVENT + 1
    AUTOMATIC_RESPOND = pygame.USEREVENT + 2
    pygame.time.set_timer(AUTOMATIC_RESPOND, params.AUTOMATIC_RESPOND_TIME, -1)
    automatic = False

    # Instanciación de la tabla y su representación gráfica.
    table_data = pandas.DataFrame(columns=('Cliente', 'Estado', 'T. Llegada','Boletas','T. Final'))
    table = view.Table(table_data, 100, 10, 100, 20, 1, 7, 2, 'Comic Sans MS', 15)
    queue_tables = []
    
    queue = logic.FIFO_Server_Queue(params.SERVER_CAPACITY)


    
    # Borré lo de las prioridades y las dejé en la clase de Priority_Server_Queue directamente
    def create_new_client(id: str, n_requests: int) -> None:
        """Crea un nuevo cliente para uso del programa."""

        queue_client = logic.Queue_Client(id,n_requests, time)
        queue.enqueue(queue_client)
        new_table_line(queue_client)

    def new_table_line(queue_client: logic.Queue_Client, arrival_time: int = None) -> None:
        """Crea una nueva línea en la tabla con la información del cliente y el tiempo de llegada indicado."""
        table_data.loc[len(table_data)] = (
            str(queue_client.get_id()),                         # Id
            'Esperando',                                        # Estado
            time + 1 if arrival_time is None else arrival_time, # Tiempo de llegada
            queue_client.get_number_of_requests(),              # Número de solicitudes.
            None
        )
    
    def expel_table_line(queue_client: logic.Queue_Client) -> pandas.Series:
        """Devuelve una fila con la infomarción calculada tras la expulsión de un Cliente."""

        # Obtener todas las filas del Cliente.
        client_rows = table_data[table_data['Cliente'] == queue_client.get_id()].iloc

        # Agregar el tiempo final en la última.
        client_rows[-1, table_data.columns.get_loc('T. Final')] = time + 1

        # Se le resta la ráfaga ejecutada de cada fila del Cliente.
        for client_row in client_rows:
            # Sólo se restan los que tienen el mismo tiempo de llegada.
            if client_row['T. Llegada'] != client_rows[-1]['T. Llegada']:
                continue

        # Cambiar estado a expulsado.
        client_rows[-1, table_data.columns.get_loc('Estado')] = 'Expulsado'

        return client_rows[-1]

    # Clientes iniciales.
    for i in range(5):
        id = chr(ord('A') + i)
        create_new_client(id,random.randint(1,15))

    # Cliente bloqueado actualmente.
    blocked_client: logic.Queue_Client = None

    # Instanciación de etiquetas
    time_tag = view.Tag(950, 10, f'Tiempo: {time + 1}', 'Comic Sans MS', 15, 'Black')
    critical_section_tag = view.Tag(400, 150, f'En sección crítica: -', 'Comic Sans MS', 15, 'Black')
    tag_list = [
        time_tag,
        critical_section_tag
    ]

    # Instanciación de cajas de texto
    textbox_list = []

    # Instanciación de botones
    button_list = []

    automatic_button = view.Button(150, 150, 200, 30, 2, 'Encender Automático', 'Comic Sans MS', 15)
    automatic_button.box_color_idle = 'Red'
    button_list.append(automatic_button)

    # Acciones de los botones
    def automatic_button_action() -> None:
        """Activa o desactiva el modo automático."""

        global automatic
        if not automatic:
            automatic = True
            automatic_button.tag = 'Apagar Automático'
            automatic_button.box_color_idle = 'Green'
        else:
            automatic = False
            automatic_button.tag = 'Encender Automático'
            automatic_button.box_color_idle = 'Red'

    automatic_button.action = automatic_button_action

    # Ejecución del programa
    while True:
        for event in pygame.event.get():
            # Oprimir el botón de cerrar ventana.
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Atención a la cola.
            if event.type == MANUAL_RESPOND or event.type == AUTOMATIC_RESPOND and automatic:
                time += 1
                # Sólo si hay clientes en fila.
                if queue.get_size() > 1:
                    queue_client = queue.get(1)
                    queue.dequeue()

                    # Dando tiempo de llegada a Cliente actual.
                    client_row = table_data[table_data['Cliente'] == str(queue_client.get_id())].iloc[-1]
                    client_row['Estado'] = 'En Ejecución'

                    # Actulizar la nueva fila en la tabla.
                    table_data.loc[client_row.name] = client_row

                    # Cuando se terminó de atender a un cliente.
                    if queue.get_current_service() == 0 and queue.get_size() == 1 or queue.get(1) is not queue_client:
                        client_row = expel_table_line(queue_client)
                        if queue_client.is_done():
                            client_row['Estado'] = 'Terminado'
                        else:
                            new_table_line(queue_client, client_row['T. Llegada'])
                                    
                        # Actulizar la nueva fila en la tabla.
                        table_data.loc[client_row.name] = client_row

            # Hacer click en una caja de texto.
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    for textbox in textbox_list:
                        textbox.check_active()

            # Escribir en las cajas de texto.
            if event.type == pygame.KEYDOWN:
                for textbox in textbox_list:
                    textbox.add_text(event.unicode)

        # Llenar la pantalla de blanco.
        screen.fill('White')

        # Actualizando elementos.
        for button in button_list:
            button.update()

        # Simulación Semáforo
        time_tag.tag = f'Tiempo: {time}'

        # Dibujando elementos.
        for tag in tag_list:
            tag.draw(screen)

        for textbox in textbox_list:
            textbox.draw(screen)

        for button in button_list:
            button.draw(screen)
        
        table.draw(screen)
        
        for queue_table in queue_tables:
            queue_table.draw(screen)
            
        # Actualizar pantalla y esperar.
        pygame.display.update()
        clock.tick()
