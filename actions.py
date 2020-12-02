# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from datetime import datetime, date, time, timedelta
import requests
import json
import pymongo
import pika
import threading

url = 'https://botdisenio.herokuapp.com/webhooks/my_connector/webhook/' 
client = pymongo.MongoClient("mongodb+srv://mlorenzo:12345qwert@cluster0.5gulk.mongodb.net/")
db = client['mydatabase']



def pasarDatos(url, tipo):
    coll = db.eventos
    myjsonL ={ "nombre" : tipo, 'Items':[]}
    if (tipo == "TiempoTrabajoUserStory"):
        tareas = {}
        #Habria que cambiar el nombre del evento y usar tipo
        for i in coll.find({'event': 'Tarea.Cambio.Estado' },{'message': 1, '_id': 0, 'time':1 }):
            js = json.loads(i['message']) #Como message es string lo paso a json asi puedo usar los indices
            if (js['tarea_id'] not in tareas.keys()): #si no esta la agrego con un diccionario vacio
                tareas[js['tarea_id']] = {}
            if (js['estado'] == 'InProgress'): #Los cambios a to do se ignoran
                tareas[js['tarea_id']].update({'InProgress': i['time']},)
            if (js['estado'] == 'Done'):
                tareas[js['tarea_id']].update({'Done': i['time'],'user': js['user_id']})
        for i in tareas:
            if ('Done' in tareas[i].keys()): #Las que no fueron movidas a 'Done' no se pasan como dato
                sec = abs((datetime.strptime(tareas[i]['Done'],'%Y-%m-%d %H:%M:%S') - datetime.strptime(tareas[i]['InProgress'],'%Y-%m-%d %H:%M:%S')))
            myjsonL['Items'].insert(0,{'user_id':tareas[i]['user'], 'value':sec.seconds})
    else:
        for i in coll.find({'event': tipo },{'message': 1, '_id': 0 }):
            myjsonL['Items'].insert(0,json.loads(i['message']))
    myjson = {
        "message": "Enviado",
        "sender": "Chatbot-Artemisas",
        "metadata":{
            "name" : str(myjsonL)   
        }
    }
    requests_response = requests.post(url, json = myjson)
    return "Numero de datos de {} enviados: {}\n".format(tipo, len(myjsonL['items']))


'''    
def subscribe_connection_request():
    connection = pika.BlockingConnection(pika.URLParameters("amqps://urfvnqok:kDPF6YteXqwoKytSirWyl_HAisUjTGYl@woodpecker.rmq.cloudamqp.com/urfvnqok"))
    channel = connection.channel()

    #channel.exchange_declare(exchange='topic_logs', exchange_type='topic', durable=True)

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange='topic_logs', queue=queue_name, routing_key="Chatbot.PedidoConeccion")        
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    channel.start_consuming()
    
    
subscribe_connection_request()
'''
class PikaMassenger():

    exchange_name = 'topic_logs'

    def __init__(self, *args, **kwargs):
        self.conn = pika.BlockingConnection(pika.URLParameters("amqps://urfvnqok:kDPF6YteXqwoKytSirWyl_HAisUjTGYl@woodpecker.rmq.cloudamqp.com/urfvnqok"))
        self.channel = self.conn.channel()
        #self.channel.exchange_declare(exchange=self.exchange_name, exchange_type='topic')

    def consume(self, keys, callback):
        result = self.channel.queue_declare('', exclusive=True)
        queue_name = result.method.queue
        for key in keys:
            self.channel.queue_bind(
                exchange=self.exchange_name, 
                queue=queue_name, 
                routing_key=key)

        self.channel.basic_consume(
            queue=queue_name, 
            on_message_callback=callback, 
            auto_ack=True)

        self.channel.start_consuming()


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close()

def start_consumer():

    def callback(ch, method, properties, body):
        print(body.decode())
        #obj = json.loads(body.decode())
        #url = obj['url']
        url="https://botdisenio.herokuapp.com/webhooks/my_connector/webhook/"
        myjson = {"message": "hi","sender": "Chatbot-Artemisas"}
        requests_response = requests.post(url, json = myjson)
        pasarDatos(url, "TiempoLecturaUserStory")
        pasarDatos(url, "TiempoTrabajoUserStory")
        pasarDatos(url, "Recurso")
        pasarDatos(url, "ParticipacionesMeetings")

    with PikaMassenger() as consumer:
        consumer.consume(keys=["Chatbot.PedidoConeccion"], callback=callback)


consumer_thread = threading.Thread(target=start_consumer)
consumer_thread.start()
class ActionOnlineMembers(Action):

	def name(self) -> Text:
		return "action_online_members"

	def run(self, dispatcher: CollectingDispatcher,
	tracker: Tracker,
	domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		f = open('online.json',) 
		dataOnline = json.load(f) 
		rta = ""
		for i in dataOnline['online']:
			#print("{} se encuentra en {}".format(i['name'], i['sala']))        
			rta += "{} se encuentra en {} \n".format(i['name'], i['sala'])
		#dispatcher.utter_message(text="Se ejecuto accion online members: {}!".format(r.text))
		dispatcher.utter_message(text=rta)
		return []



class ActionTareasToDo(Action):

	def name(self) -> Text:
		return "action_tareas_to_do"

	def run(self, dispatcher: CollectingDispatcher,
	tracker: Tracker,
	domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		f = open('tareas.json',) 
		dataOnline = json.load(f)
		rta = ""
		rta += "Las tareas en estado to do son:\n"
		for i in dataOnline['to_do']:       
			rta+="--Tarea: {}. Nombre {}.\n Descripcion: {}.\n Criterios de aceptacion: {}\n".format(i['id_tarea'],i['nombre'], i['descripcion'], i['criterios de aceptacion'])
		rta += "\nQuieres asignarte alguna tarea?"
		dispatcher.utter_message(text=rta)
		return []

class ActionTareasInProgress(Action):

	def name(self) -> Text:
		return "action_tareas_in_progress"

	def run(self, dispatcher: CollectingDispatcher,
	tracker: Tracker,
	domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		f = open('tareas.json',)
		dataOnline = json.load(f)
		rta = ""
		rta += "Las tareas en estado in progress son:\n"
		for i in dataOnline['in_progress']:     
			rta+="--Tarea: {}. Nombre {}.\n Descripcion: {}.\n Criterios de aceptacion: {}\n Participantes: {}\n".format(i['id_tarea'],i['nombre'], i['descripcion'], i['criterios de aceptacion'],i['participantes'])
		dispatcher.utter_message(text=rta)
		return []

class ActionTareasDone(Action):

	def name(self) -> Text:
		return "action_tareas_done"

	def run(self, dispatcher: CollectingDispatcher,
	tracker: Tracker,
	domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		f = open('tareas.json',) 
		dataOnline = json.load(f)
		rta = ""
		rta += "Las tareas en estado done son:\n"
		for i in dataOnline['done']:
			rta+="--Tarea: {}. Nombre {}.\n Descripcion: {}.\n Criterios de aceptacion: {}\n".format(i['id_tarea'],i['nombre'], i['descripcion'], i['criterios de aceptacion'])
		dispatcher.utter_message(text=rta)
		return []


class ActionOrganizacionActual(Action):

	def name(self) -> Text:
		return "action_organizacion_actual"

	def run(self, dispatcher: CollectingDispatcher,
	tracker: Tracker,
	domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		f = open('organizacion.json',) 
		dataOnline = json.load(f) 
		dataOnline = dataOnline['sprint']
		rta = ""
		rta += "En el sprint {}, las tareas estan organizadas segun los siguientes grupos:\n".format(dataOnline['numero'])
		for i in dataOnline['equipos']:
			rta += "--Grupo: {}. Cuyo lider es: {}".format(i['grupo'], i['lider'])
		dispatcher.utter_message(text=rta)
		return []


class ActionMiTarea(Action):

	def name(self) -> Text:
		return "action_mi_tarea"

	def run(self, dispatcher: CollectingDispatcher,
	tracker: Tracker,
	domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		f = open('tareas.json',)
		dataOnline = json.load(f)
		#dispatcher.utter_message(text=tracker.sender_id)
		asignada = False
		user = "Mercedes"  #Alguna forma de obtener el id del usuario
		for i in dataOnline['in_progress']:
			if (user in i['participantes']):
				dispatcher.utter_message(text="Tienes la tarea {} asignada para hoy.".format(i['nombre']))
				asignada = True
		if(asignada == False):
			dispatcher.utter_message(text="No tienes ninguna tarea asignada, debes revisar las tareas en estado to do y tomar una")
		return []


class ActionAsignarTarea(Action):

	def name(self) -> Text:
		return "action_asignar_tarea"

	def run(self, dispatcher: CollectingDispatcher,
	tracker: Tracker,
	domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		f = open('tareas.json',)
		dataOnline = json.load(f)
		nombre= ''
		descrip = ''
		criterios = []
		participantes = ['Mercedes']
		if (tracker.get_slot("id_tarea") != None):
			id = tracker.get_slot("id_tarea")
			aux = dataOnline['to_do']
			for i in aux:
				if (i['id_tarea'] == id):
					nombre = i['nombre']
					descrip = i['descripcion']
					criterios = i['criterios de aceptacion']
					dataOnline['to_do'].remove(i)
					break
		if (nombre != ''):
			dataOnline['in_progress'].append({
				'id_tarea':id,
				'nombre':nombre,
				'descripcion':descrip,
				'criterios de aceptacion':criterios,
				'participantes':participantes
			})
			dispatcher.utter_message(text='La tarea con id: {} fue correctamente asignada'.format(id))
		else:
			dispatcher.utter_message(text='No hay una tarea con ese id')	
		with open('tareas.json', 'w') as outfile:
			json.dump(dataOnline, outfile)
		return []




class ActionNuevaReunion(Action):

	def name(self) -> Text:
		return "action_nueva_reunion"

	def run(self, dispatcher: CollectingDispatcher,
	tracker: Tracker,
	domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		#dispatcher.utter_message(text=tracker.sender_id)
		
		hora = tracker.get_slot("horario")
		if (hora != None):
			hoy = datetime.now()
			h = int(hora[0:hora.index(':')])
			m = int(hora[hora.index(':')+1:])
			hoy = hoy.replace(hour=h)
			hoy = hoy.replace(minute=m)
			coll = db.reuniones
			my_dict = my_dict = {
				'numero': coll.count(),
				'fecha': "{}".format(hoy.strftime("%x")),
				'horario': "{}:{}".format(hoy.strftime("%H"),hoy.strftime("%H"))
				}
			if (tracker.get_slot("descripcion") != None):
				my_dict = {
				'numero': coll.count(),
				'fecha': "{}".format(hoy.strftime("%x")),
				'horario': "{}:{}".format(hoy.strftime("%H"),hoy.strftime("%H")),
				'descripcion':tracker.get_slot("descripcion")
				}
			coll.insert_one(my_dict)
			dispatcher.utter_message(text="Programaste una reunion para hoy a las {}:{} hs, \nQuieres que me encargue de programarla en los proximos dias?".format(hoy.strftime("%H"),hoy.strftime("%M")))
		return []



class ActionNuevoSprint(Action):

	def name(self) -> Text:
		return "action_nuevo_sprint"

	def run(self, dispatcher: CollectingDispatcher,
	tracker: Tracker,
	domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		if (tracker.get_slot("fecha_fin") != None):
			fecha_fin = datetime.strptime(tracker.get_slot("fecha_fin"), '%d/%m/%Y')
			coll = db.sprint
			myquery = { "estado": "activo" }
			newvalues = { "$set": { "estado": "inactivo" } }
			x = coll.update_many(myquery, newvalues)
			my_dict = {
				'numero': coll.count(),
				'fecha_fin': tracker.get_slot("fecha_fin"),
				'estado': 'activo'
			}
			coll.insert_one(my_dict)
			dispatcher.utter_message(text="El nuevo sprint finaliza el {} \nQuieres que me encargue de programar las daily y la retropective?".format(fecha_fin.strftime("%x")))
		return []



class ActionSprintActual(Action):

	def name(self) -> Text:
		return "action_sprint_actual"

	def run(self, dispatcher: CollectingDispatcher,
	tracker: Tracker,
	domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		myquery = { "estado": "activo" }
		coll = db.sprint
		res = coll.find_one(myquery)
		if (res != None):
			dispatcher.utter_message(text='Sprint actual numero {}, termina el dia {}'.format(res['numero'],res['fecha_fin']))
		else:
			dispatcher.utter_message(text='No hay un sprint activo')
		return []


class ActionProgramarDailys(Action):

	def name(self) -> Text:
		return "action_programar_dailys"

	def run(self, dispatcher: CollectingDispatcher,
	tracker: Tracker,
	domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		tomorrow = datetime.today() + timedelta(days = 1)
		hora = tracker.get_slot("horario")
		if ((hora != None) and (tracker.get_slot("fecha_fin"))):
			tomorrow = tomorrow.replace(hour=int(hora[0:hora.index(":")]))
			tomorrow = tomorrow.replace(minute=int(hora[hora.index(":")+1:]))
			fecha_fin = datetime.strptime(tracker.get_slot("fecha_fin"), '%d/%m/%Y')
			coll = db.reuniones
			while (tomorrow < fecha_fin):
				my_dict = {
					'numero': coll.count(),
					'fecha': "{}".format(tomorrow.strftime("%x")),
					'horario': "{}:{}".format(tomorrow.strftime("%H"),tomorrow.strftime("%H")),
					'descripcion':"Reunion daily"
					}
				coll.insert_one(my_dict)
				#dispatcher.utter_message(text="Daily reunion el dia {} a las {}:{}hs".format(tomorrow.strftime("%x"),tomorrow.strftime("%H"),tomorrow.strftime("%M")))
				tomorrow += timedelta(days = 1)
			my_dict = {
				'numero': coll.count(),
				'fecha': "{}".format(tomorrow.strftime("%x")),
				'horario': "{}:{}".format(tomorrow.strftime("%H"),tomorrow.strftime("%H")),
				'descripcion':"Reunion retrospective"
				}
			coll.insert_one(my_dict)
			dispatcher.utter_message(text="Las reuniones fueron agendadas con exito")
		return []


class ActionProgramarReuniones(Action):

	def name(self) -> Text:
		return "action_programar_reuniones"

	def run(self, dispatcher: CollectingDispatcher,
	tracker: Tracker,
	domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		tomorrow = datetime.today() + timedelta(days = 1)
		hora = tracker.get_slot("horario")
		if ((hora != None) and (tracker.get_slot("fecha_fin"))):
			tomorrow = tomorrow.replace(hour=int(hora[0:hora.index(":")]))
			tomorrow = tomorrow.replace(minute=int(hora[hora.index(":")+1:]))
			fecha_fin = datetime.strptime(tracker.get_slot("fecha_fin"), '%d/%m/%Y')
			coll = db.reuniones
			while (tomorrow <= fecha_fin):
				my_dict = {
					'numero': coll.count(),
					'fecha': "{}".format(tomorrow.strftime("%x")),
					'horario': "{}:{}".format(tomorrow.strftime("%H"),tomorrow.strftime("%H"))
					}
				coll.insert_one(my_dict)
				#dispatcher.utter_message(text="Daily reunion el dia {} a las {}:{}hs".format(tomorrow.strftime("%x"),tomorrow.strftime("%H"),tomorrow.strftime("%M")))
				tomorrow += timedelta(days = 1)
			dispatcher.utter_message(text="Las reuniones fueron agendadas con exito")
		return []



class ActionProximasReuniones(Action):

	def name(self) -> Text:
		return "action_proximas_reuniones"

	def run(self, dispatcher: CollectingDispatcher,
	tracker: Tracker,
	domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		hoy = datetime.today()
		coll = db.reuniones
		res = 'Estas son las proximas cinco reuniones: \n'
		for i in coll.find({'fecha': { "$gte": "{}".format(hoy.strftime("%x")) }}).sort('fecha',1).limit(5):
			if (i['descripcion'] != None):
				res += "{} a las {}. Descripcion: {}\n".format(i['fecha'], i['horario'], i['descripcion'])
			else:
				res += "{} a las {}\n".format(i['fecha'], i['horario']) 
		dispatcher.utter_message(text=res)
		return []


class ActionEmpezarReunion(Action):

	def name(self) -> Text:
		return "action_empezar_reunion"

	def run(self, dispatcher: CollectingDispatcher,
	tracker: Tracker,
	domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		hoy = datetime.today()
		coll = db.reuniones
		id = tracker.get_slot('id_reunion')
		res = 'Da comienzo la reunion: \n'
		res = coll.find_one({'numero': id })
		if (res != None):
			dispatcher.utter_message(text= 'Da comienzo la reunion: {} \nDescripcion: {}'.format(res['numero'],res['descripcion']))
		else:
			dispatcher.utter_message(text= 'No hay una reunion cargada con ese id')
		return []

class ActionPasarDatos(Action):

	def name(self) -> Text:
		return "action_pasar_datos"

	def run(self, dispatcher: CollectingDispatcher,
	tracker: Tracker,
	domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		myobj = {
			"message": "hi",
			"sender": "usuario"
		}
		request_response = request.post(url, json = myobj)
		coll = db.datos
		mensaje = 'Enviado'
		consulta = db.datos.find_one({"nombre" : "Usuarios"})
		if (consulta != None):
			myjson = {
			'nombre' : consulta['nombre'],
			'Items' : consulta['Items']
			}
		else: 
			myjson = ''
		myobj = {
			"message": str(mensaje),
			"sender": "usuario",
			"metadata":{
				"name": str(myjson)
			}
		}
		request_response = requests.post(url, json = myobj)
		consulta = db.datos.find_one({"nombre" : "TiempoLecturaUserStory"})
		if (consulta != None):
			myjson = {
			'nombre' : consulta['nombre'],
			'Items' : consulta['Items']
			}
		else: 
			myjson = ''
		myobj = {
			"message": str(mensaje),
			"sender": "usuario",
			"metadata":{
				"name": str(myjson)
			}
		}
		request_response = requests.post(url, json = myobj)
		consulta = db.datos.find_one({"nombre" : "TiempoTrabajoUserStory"})
		if (consulta != None):
			myjson = {
			'nombre' : consulta['nombre'],
			'Items' : consulta['Items']
			}
		else: 
			myjson = ''
		myobj = {
			"message": str(mensaje),
			"sender": "usuario",
			"metadata":{
				"name": str(coll.find(myjson))
			}
		}
		request_response = requests.post(url, json = myobj)
		consulta = db.datos.find_one({"nombre" : "Recurso"})
		if (consulta != None):
			myjson = {
			'nombre' : consulta['nombre'],
			'Items' : consulta['Items']
			}
		else: 
			myjson = ''
		myobj = {
			"message": str(mensaje),
			"sender": "usuario",
			"metadata":{
				"name": str(myjson)
			}
		}
		request_response = requests.post(url, json = myobj)
		consulta = db.datos.find_one({"nombre" : "ParticipacionesMeetings"})
		if (consulta != None):
			myjson = {
			'nombre' : consulta['nombre'],
			'Items' : consulta['Items']
			}
		else: 
			myjson = ''
		myobj = {
			"message": str(mensaje),
			"sender": "usuario",
			"metadata":{
				"name": str(myjson)
			}
		}
		request_response = requests.post(url, json = myobj)
		return []
