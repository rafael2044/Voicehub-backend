import json
from typing import Dict
from datetime import datetime
from fastapi import WebSocket
from app.crud.message import save_message
from app.crud.calls import save_call_record

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_status: Dict[str, str] = {}
        self.user_names: Dict[str, str] = {} # NOVO: Dicionário para guardar os nomes reais
        self.active_calls_data: Dict[str, dict] = {}

    # MUDANÇA: Agora recebe o user_name na hora de conectar
    async def connect(self, websocket: WebSocket, user_id: str, user_name: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_status[user_id] = "online"
        self.user_names[user_id] = user_name # Memoriza o nome
        await self.broadcast_user_list()

    def disconnect(self, user_id: str):
        if user_id in self.active_calls_data:
            partner = self.active_calls_data[user_id]['partner']
            # Cria uma task assíncrona para não travar o método síncrono
            import asyncio
            asyncio.create_task(self.stop_call_tracking(user_id))
            
            # Avisa o parceiro que a ligação caiu por falta de conexão
            if partner in self.active_connections:
                import json
                asyncio.create_task(
                    self.active_connections[partner].send_text(
                        json.dumps({"type": "call_ended", "reason": "connection_lost"})
                    )
                )
        if user_id in self.active_connections: del self.active_connections[user_id]
        if user_id in self.user_status: del self.user_status[user_id]
        if user_id in self.user_names: del self.user_names[user_id] # Limpa o nome
        if user_id in self.active_calls_data: del self.active_calls_data[user_id]
        
    async def broadcast_user_list(self):
        # MUDANÇA: Puxa o nome real do usuário em vez de repetir o ID
        users_list = [{"id": uid, "name": self.user_names.get(uid, uid), "status": status} for uid, status in self.user_status.items()]
        msg = json.dumps({"type": "user_list", "users": users_list})
        for conn in self.active_connections.values():
            try: await conn.send_text(msg)
            except: pass
    
    async def broadcast_mural(self, mural_data):
        msg = json.dumps({"type": "mural_update", "data": mural_data})
        for conn in self.active_connections.values():
            try: await conn.send_text(msg)
            except: pass

    async def send_private(self, message: dict, target_id: str):
        if target_id in self.active_connections:
            await self.active_connections[target_id].send_text(json.dumps(message))

    # MUDANÇA: Convertendo IDs para int() exclusivamente na hora de salvar no banco
    async def inject_system_message(self, sender_id: str, recipient_id: str, text: str):
        await save_message(int(sender_id), int(recipient_id), text, "system")
        msg_payload = {"type": "private_chat", "sender": sender_id, "content": text, "msg_type": "system"}
        await self.send_private(msg_payload, recipient_id)
        await self.send_private({
            "type": "private_chat_sent", 
            "recipient": recipient_id, 
            "content": text, 
            "msg_type": "system"
        }, sender_id)

    def set_status(self, user_id: str, status: str):
        self.user_status[user_id] = status

    def start_call_tracking(self, caller, callee):
        self.active_calls_data[caller] = {'start': None, 'partner': callee, 'role': 'caller', 'accepted': False}
        self.active_calls_data[callee] = {'start': None, 'partner': caller, 'role': 'callee', 'accepted': False}

    def mark_call_accepted(self, user_id):
        if user_id in self.active_calls_data:
            start = datetime.now()
            self.active_calls_data[user_id]['start'] = start
            self.active_calls_data[user_id]['accepted'] = True
            partner = self.active_calls_data[user_id]['partner']
            if partner in self.active_calls_data:
                self.active_calls_data[partner]['start'] = start
                self.active_calls_data[partner]['accepted'] = True

    async def stop_call_tracking(self, user_id: str):
        if user_id in self.active_calls_data and self.active_calls_data[user_id]['accepted']:
            data = self.active_calls_data[user_id]
            start_time = data['start']
            partner = data['partner']
            role = data['role']
            accepted = data['accepted']
            end_time = datetime.now()
            
            delta = end_time - start_time
            total_seconds = int(delta.total_seconds())
            mins, secs = divmod(total_seconds, 60)
            duration_str = f"{mins:02}:{secs:02}"
            
            db_caller = user_id if role == 'caller' else partner
            db_callee = partner if role == 'caller' else user_id

            status_call = "completed" if accepted else "missed"
            
            # MUDANÇA: Convertendo IDs para int() na hora de chamar a função do banco
            await save_call_record(int(db_caller), int(db_callee), start_time, end_time, duration_str, status_call)
                      
            if user_id in self.active_calls_data: del self.active_calls_data[user_id]
            if partner in self.active_calls_data: del self.active_calls_data[partner]
            
            return accepted
        return False

manager = ConnectionManager()