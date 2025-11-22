import json

class NodeRegistry:
    def __init__(self, registry_file="nodes.json"):
        self.registry_file = registry_file
        try:
            with open(registry_file, "r") as f:
                self.nodes = json.load(f)
        except:
            self.nodes = {}

    def add_node(self, node_id, addr):
        self.nodes[node_id] = addr
        self._save()

    def remove_node(self, node_id):
        if node_id in self.nodes:
            del self.nodes[node_id]
            self._save()

    def list_nodes(self):
        return self.nodes

    def _save(self):
        with open(self.registry_file, "w") as f:
            json.dump(self.nodes, f, indent=2)
