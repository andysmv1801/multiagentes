import random
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer

# Direcciones para los carriles verticales y horizontales.
Direccion_vertical = [(0, 1)]
Direccion_horizontal = [(1, 0), (-1, 0)]  # Direcciones opuestas.

# Definir el agente para los carros.
class Carro(Agent):
    def __init__(self, unique_id, model, tipo_carril=None, direccion=None):
        super().__init__(unique_id, model)
        self.tipo_carril = tipo_carril
        self.direccion = direccion
        self.esquina = False  

    def move(self):
        x, y = self.pos
        dx, dy = self.direccion[0], self.direccion[1]
        next_x, next_y = x + dx, y + dy

        width, height = self.model.grid.width, self.model.grid.height

        if (0 <= next_x < width and 0 <= next_y < height and self.tipo_carril[next_x][next_y]):
            if (next_x == 0 or next_x == width - 1 or next_y == 0 or next_y == height - 1):
                self.esquina = True
                next_x = (next_x + width // 2) % width
                next_y = (next_y + height // 2) % height
            self.model.grid.move_agent(self, (next_x, next_y))

    def en_interseccion(self, x, y):
        width, height = self.model.grid.width, self.model.grid.height
        return (width // 2 - 2 <= x <= width // 2 + 2) or (height // 2 - 2 <= y <= height // 2 + 2)

# Definir el agente semáforo.
class Semaforo(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.en_vertical = True

    def step(self):
        pass

# Definir el modelo de la intersección.
class Interseccion(Model):
    def __init__(self, width, height, num_carros, semaforo_duracion=10):
        self.num_agents = num_carros
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)
        self.semaforo_duracion = semaforo_duracion
        self.vertical_permitido = True  
        self.movs = 0  

        tipo_carril = [[0] * height for _ in range(width)]

        for i in range(width):
            if i in range((width - 3) // 2, (width + 3) // 2):
                for j in range(height):
                    tipo_carril[i][j] = 1

        for j in range(height):
            if j in range((height - 3) // 2, (height + 3) // 2):
                for i in range(width):
                    tipo_carril[i][j] = 1

        carril_contrario = random.choice(range((height - 3) // 2, (height + 3) // 2))
        for i in range(width):
            tipo_carril[i][carril_contrario] = 0
        for i in range((width - 3) // 2, (width + 3) // 2):
            tipo_carril[i][carril_contrario] = 1

        for i in range((width - 3) // 2, (width + 3) // 2):
            for j in range((height - 3) // 2, (height + 3) // 2):
                tipo_carril[i][j] = 1

        for i in range(num_carros):
            x, y = self.posicion_permitida(tipo_carril, width, height)
            direccion = random.choice(Direccion_vertical + Direccion_horizontal)
            agent = Carro(i, self, tipo_carril=tipo_carril, direccion=direccion)
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)

        self.semaforo = Semaforo(-1, self)
        self.grid.place_agent(self.semaforo, (width // 2, height // 2))
        self.schedule.add(self.semaforo)
        self.semaforo_duracion = semaforo_duracion
        self.vertical_permitido = True

    def posicion_permitida(self, tipo_carril, width, height):
        while True:
            x = random.randrange(width)
            y = random.randrange(height)
            if tipo_carril[x][y]:
                return x, y

    def step(self):
        self.movs += 1
        
        if self.movs % self.semaforo_duracion == 0:
            self.vertical_permitido = not self.vertical_permitido
            self.semaforo.en_vertical = not self.semaforo.en_vertical
        
        for agent in self.schedule.agents:
            if isinstance(agent, Carro):      
                if (agent.direccion in Direccion_vertical and self.semaforo.en_vertical) or (agent.direccion in Direccion_horizontal and not self.semaforo.en_vertical):
                    agent.move()

def agent_portrayal(agent):
    if isinstance(agent, Carro):
        portrayal = {"Shape": "circle", "Color": "red", "Filled": "true", "Layer": 0, "r": 0.5}
    elif isinstance(agent, Semaforo):
        if agent.en_vertical:
            portrayal = {"Shape": "rect", "Color": "green", "Filled": "true", "Layer": 0, "w": 0.5, "h": 0.5}
        else:
            portrayal = {"Shape": "rect", "Color": "red", "Filled": "true", "Layer": 0, "w": 0.5, "h": 0.5}
    else:
        portrayal = None
    x, y = agent.pos
    portrayal["x"] = x
    portrayal["y"] = y
    return portrayal

grid = CanvasGrid(agent_portrayal, 15, 15, 500, 500)

model = Interseccion(15, 15, 10, semaforo_duracion=10)  
server = ModularServer(
    Interseccion, [grid], "Intersection Model", {"width": 15, "height": 15, "num_carros": 10, "semaforo_duracion":10}
)
server.port = 8522  
server.launch()

