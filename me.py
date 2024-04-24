import simpy
import networkx as nx
import matplotlib.pyplot as plt
import random
import time

class Network:
    def __init__(self, env):
        self.env = env
        self.nodes = []

    def add_node(self, node):
        self.nodes.append(node)

    def get_total_nodes(self):
        return len(self.nodes)

class Node:
    def __init__(self, network, name):
        self.network = network
        self.name = name
        self.neighbors = []
        self.address = f"Node{self.network.get_total_nodes() + 1}"
        self.parent = None
        self.children = []
        self.dao_sent = False
        self.dis_sent = False
        self.dis_timer = None
        self.dis_interval = 1 # Start with a 1-second interval for the trickle algorithm
        self.dis_backoff = 0.5 # Backoff factor for the trickle algorithm

    def add_neighbor(self, neighbor):
        self.neighbors.append(neighbor)

    def send_dao(self, env):
        if not self.dao_sent:
            print(f"{self.name} sends DAO to {self.parent.name}")
            self.dao_sent = True
            yield env.timeout(1)

    def receive_dio(self, env):
        print(f"{self.name} receives DIO from {self.children[0].name}")
        yield env.timeout(1)

    def send_dis(self, env):
        if not self.dis_sent:
            print(f"{self.name} sends DIS")
            self.dis_sent = True
            # Trickle algorithm: Use the current dis_interval for the timer
            self.dis_timer = env.timeout(self.dis_interval)
            yield self.dis_timer
            self.dis_sent = False
            # Trickle algorithm: Double the interval for the next DIS message
            self.dis_interval *= 2
            # Trickle algorithm: Add a random backoff factor
            self.dis_interval += random.uniform(-self.dis_backoff, self.dis_backoff)

def run_simulation(num_nodes):
    start_time = time.time() # Capture the start time

    env = simpy.Environment()
    network = Network(env)

    # Create the root node
    root_node = Node(network, "node1")
    network.add_node(root_node)

    # Dynamically create nodes and assign parents
    current_parent = root_node
    for i in range(2, num_nodes + 1):
        node_name = f"node{i}"
        new_node = Node(network, node_name)
        network.add_node(new_node)
        new_node.parent = current_parent
        current_parent.children.append(new_node)

        # Randomly assign additional children to the current node
        if i < num_nodes:
            num_children = random.randint(1, num_nodes - i)
            for _ in range(num_children):
                child_node = Node(network, f"node{i+_+1}")
                network.add_node(child_node)
                child_node.parent = new_node
                new_node.children.append(child_node)

        current_parent = new_node

    # Simulate DAO and DIO process
    for node in network.nodes:
        if node.parent is not None:
            env.process(node.send_dao(env))
        if node.children:
            env.process(node.receive_dio(env))

    # Simulate DIS message using the trickle algorithm
    for node in network.nodes:
        env.process(node.send_dis(env))

    # Run the simulation
    env.run()

    end_time = time.time() # Capture the end time
    print(f"Simulation took {end_time - start_time} seconds to run.")

    # Visualize the DODAG structure
    visualize_dodag(network)

def visualize_dodag(network):
    G = nx.DiGraph()
    for node in network.nodes:
        if node.parent is not None:
            G.add_edge(node.parent.name, node.name)
        for child in node.children:
            G.add_edge(node.name, child.name)

    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=500, font_size=5, font_weight='bold')
    plt.title('DODAG Structure')
    plt.show()

if __name__ == "__main__":
    run_simulation(100) # Adjust the number of nodes as needed
