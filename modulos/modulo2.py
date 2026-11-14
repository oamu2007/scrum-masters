import numpy as np

# Esta funcion la necesitaremos para la funcion de abajo, convierte la lista de ventanas
# del modulo 4 en un arreglo booleano, donde True significa que el juego esta parado

def periodosDetenido(n_frames, restart_windows_list):
    # Para experimentar pueden cambiar n_frames por el len() de los arreglos generados
    detenido = np.zeros(n_frames, dtype=bool)
    
    for w in restart_windows_list:
        inicio = w["start_frame"]
        fin = w["end_frame"]
        if inicio is not None and fin is not None:
            detenido[max(0, inicio):min(n_frames, fin + 1)] = True
            
    return detenido

# Para usar esta funcion hagan un file llamado main en donde extraigan los datos del CSV
# del modulo 1 en variables, esas variables se las pasan a esta funcion

def modulo_2(s_home, s_away, visible_ball, restart_windows_list, total_frames, valid_halves_mask=None):
    # Transformamos las ventanas del modulo 4 en un arreglo de paradas por frame
    noEnJuego = periodosDetenido(total_frames, restart_windows_list)
    etiquetas = []
    control_actual = 'D'  # Iniciamos en D porque nadie tiene posesion en el momento, realmente creo que esto no deberia efectar mucho si se pone otra cosa
    for i in range(total_frames):
        # Revisa si el los frames revisados estan en tiempo de juego
        # si no, agrega una x a las etiquetas, esto no lo pide el modulo (no se porque)
        # por lo que lo pueden alterar para que se solo un continue (es decir comentar la linea etiqeutas.append(X))
        # O eliminar las x despues de hacer todo el arreglo
        enTiempoReglamentario = valid_halves_mask[i] if valid_halves_mask is not None else True
        if not enTiempoReglamentario:
            etiquetas.append('X')
            continue

        # Revisa la si el frame esta la lista del modulo 4 de periodos parados
        # si lo esta agrega una D
        if noEnJuego[i]:
            etiquetas.append('D')
            continue

        # Los scores para cada frame, obtenidos del modulo 1    
        visible = visible_ball[i]
        sh = s_home[i]
        sa = s_away[i]
        
        if visible == 0 or (sh == 0.0 and sa == 0.0): # Si el balon no es visible, la etiquea anterior se mantiene
            control_previo = control_actual
        elif sh > sa: # Si el local esta mas cerca que el visitante
            control_previo = 'H'
            control_actual = 'H'  # Actualizamos memoria
        elif sa > sh: # Si el visitante esta mas cerca del local
            control_previo = 'A'
            control_actual = 'A'  # Actualizamos memoria
        else: # si son iguales la posesion se maniene igual
            control_previo = control_actual

        #Guardamos las todas las etiquetas generadas
        etiquetas.append(control_previo)
    # Devolvermos la lista final
    return etiquetas

# Comentario general: esta funcion se debe testear en el pipeline final, puede que la logia
# sa > sh y sh > sa sea demasiado simple para lo complejo que pueda ser definir si un equipo tiene posesion o no
# pero primero hay que probar que funcione