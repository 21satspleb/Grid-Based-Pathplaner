from typing import Optional, Tuple
import math
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from vectorGrid import VectorGrid
import networkx as nx
from geopandas.tools import sjoin

class GraphGrid:
    """
    The GraphGrid class is used to create a graph from a grid of geographical data.
    It uses networkx to create the graph and geopandas for spatial operations.
    """
    def __init__(self, grid):
        """
        Initializes a GraphGrid instance.
        
        Parameters:
        grid (GeoDataFrame): A GeoDataFrame representing the grid.
        """
        self.grid = grid
        self.graph = self.create_graph()
        self.start_id = None
        self.end_id = None
        self.path = None

    def create_graph(self):
        """
        Creates a graph from the grid where each node represents a cell in the grid 
        and each edge represents adjacency between two cells.
        
        Returns:
        networkx.Graph: A graph representing the grid.
        """
        # Create an empty graph
        G = nx.Graph()

        # Add a node for each cell in the grid
        for index, row in self.grid.iterrows():
            if row['passable']:
                G.add_node(row['id'], geometry=row['geometry'])

        # Create a new GeoDataFrame that includes slightly expanded versions of each cell
        grid_expanded = self.grid.copy()
        grid_expanded['geometry'] = grid_expanded['geometry'].buffer(1)  # Adjust the buffer distance as needed

        # Perform a spatial join between the original grid and the expanded grid
        joined = sjoin(self.grid, grid_expanded, how='inner', op='intersects')

        # For each cell in the original grid, add an edge between the cell and each of its neighbors
        for cell_id, neighbors in joined.groupby('id_left'):
            if cell_id in G.nodes:  # Check if the cell is in the graph
                for neighbor_id in neighbors['id_right']:
                    if cell_id != neighbor_id and neighbor_id in G.nodes:  # Exclude the cell itself and non-passable neighbors
                        # Calculate the weight as the Euclidean distance between the centers of the two cells
                        weight = G.nodes[cell_id]['geometry'].centroid.distance(G.nodes[neighbor_id]['geometry'].centroid)
                        G.add_edge(cell_id, neighbor_id, weight=weight)

        return G

    def find_path(self, start_id, end_id):
        """
        Finds the shortest path from the start node to the end node using the A* algorithm.
        
        Parameters:
        start_id (int): The ID of the start node.
        end_id (int): The ID of the end node.
        
        Returns:
        list, optional: A list of node IDs representing the shortest path from start to end. 
        If no path is found, returns None.
        """
        if start_id not in self.graph.nodes:
            raise ValueError(f"Start point {start_id} is not in the graph.")
        if end_id not in self.graph.nodes:
            raise ValueError(f"End point {end_id} is not in the graph.")
        self.start_id = start_id
        self.end_id = end_id
        self.path = nx.astar_path(self.graph, start_id, end_id, weight='weight')
        return self.path


    def visualize_path(self):
        """
        Visualizes the grid and the path from the start node to the end node.
        Raises an error if find_path() has not been called.
        
        Raises:
        ValueError: If a path has not been computed yet.
        """
        if self.path is None or self.start_id is None or self.end_id is None:
            raise ValueError("You must call find_path() before visualize_path().")

        path_cells = self.grid[self.grid['id'].isin(self.path)]

        fig, ax = plt.subplots()
        if self.grid['passable'].any():  # If there are any passable cells
            self.grid[self.grid['passable']].plot(ax=ax, color='green', edgecolor='black')
        if (~self.grid['passable']).any():  # If there are any impassable cells
            self.grid[~self.grid['passable']].plot(ax=ax, color='red', edgecolor='black')
        path_cells.plot(ax=ax, color='blue', edgecolor='black')  # Plot path cells in blue
        self.grid[self.grid['id'] == self.start_id].plot(ax=ax, color='gold', edgecolor='black')  # Plot start cell in gold
        self.grid[self.grid['id'] == self.end_id].plot(ax=ax, color='magenta', edgecolor='black')  # Plot end cell in magenta 
        legend_elements = [Patch(facecolor='green', edgecolor='black', label='Passable'),
                           Patch(facecolor='red', edgecolor='black', label='Impassable'),
                           Patch(facecolor='gold', edgecolor='black', label='Start'),
                           Patch(facecolor='blue', edgecolor='black', label='Path'),
                           Patch(facecolor='magenta', edgecolor='black', label='End')]
        ax.legend(handles=legend_elements, loc=3)
        plt.title('A* Path Visualization')
        plt.xlabel('Easting (m)')
        plt.ylabel('Northing (m)')
        plt.show()

# # Testing
# # Load geojson 
# polygon = gpd.read_file('data/demo_boundary.geojson')
# polygon = convert_to_utm(polygon)

# obstacles = gpd.read_file('data/obstacles.geojson')
# obstacles = convert_to_utm(obstacles)

# # Create a VectorGrid
# vg = VectorGrid(polygon=polygon, cell_size=25, obstacle=obstacles)
# vg.intersect()
# vg.visualize()
# # Create a GraphGrid from the VectorGrid's grid
# gg = GraphGrid(vg.grid)

# print(vg.grid.head(500))

# # Get the IDs of the start and end nodes
# start_id = 1
# end_id = vg.closest_cell_id((513314,4645748))

# # Find the shortest path from the start node to the end node
# gg.find_path(start_id, end_id)

# # # Visualize the grid and the path from the start node to the end node
# gg.visualize_path()
