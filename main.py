import warnings
from vectorGrid import VectorGrid
from GraphGrid import GraphGrid
import os
import geopandas as gpd
import matplotlib.pyplot as plt
from colorama import Fore, Style

plt.ion()  # Turn on interactive mode
warnings.filterwarnings('ignore')  # Ignore warnings

def main():
    boundary = None
    obstacles = None
    grid = None
    graph = None
    start_point = None
    end_point = None
    path = None
    boundary_file_path = None
    obstacle_file_path = None

    while True:
        print('********************************************************')
        print('* Grid-Based Pathplaner with Graph and A* Algorithm    ')
        print('* Author: Julius Petri')
        print(f'* Boundary loaded : {boundary is not None}', end="")
        if boundary is not None:
            print(f'{Fore.GREEN}  Path: {boundary_file_path}{Style.RESET_ALL}')
        else:
            print()
        print(f'* Obstacles loaded: {obstacles is not None}', end="")
        if obstacles is not None:
            print(f'{Fore.GREEN}  Path: {obstacle_file_path}{Style.RESET_ALL}')
        else:
            print()
        print(f'* Grid Initialied: {grid is not None}', end="")
        if grid is not None:
            print(f'{Fore.BLUE}  Parameters: Cell size = {cell_size}, Rotation = {rotation}')
            print(f'  Number of rows: {len(grid)}{Style.RESET_ALL}')
        else:
            print()
        print(f'* Graph Initialized: {graph is not None}', end="")
        if graph is not None:
            print(f'{Fore.YELLOW}  Number of nodes: {len(graph.nodes)}')
            print(f'  Number of edges: {len(graph.edges)}{Style.RESET_ALL}')
        else:
            print()
        print('********************************************************')
        print('\nWhat do you want to do?')
        print('1) Load boundary and obstacles')
        print('2) Generate grid and graph')
        print('3) Generate path')
        print('4) Quit')

        option = input('Enter the number of your choice: ')

        if option == '1':
            # Load boundary and obstacles
            files = os.listdir('data/')
            print('Available files:')
            for i, file in enumerate(files, start=1):
                print(f'{i}) {file}')
            # Prompt user to select a boundary          
            boundary_file  = int(input('Enter the number for the boundary file: '))
            boundary_file_path = f'data/{files[int(boundary_file)-1]}'
            boundary = gpd.read_file(boundary_file_path)
            # Check if boundary is a multipolygon
            if boundary.geometry.iloc[0].type == 'MultiPolygon':
                print(f"{Fore.RED} \n Multipolygons are not allowed as boundaries. Please select a valid boundary file.{Style.RESET_ALL} \n")
                boundary = None
                continue
          
            # Prompt user to select a obstacle
            obstacle_file = int(input('Enter the number for the obstacle file: '))
            if obstacle_file:
                obstacle_file_path = f'data/{files[int(obstacle_file)-1]}'
                obstacles = gpd.read_file(obstacle_file_path)
            print("\n")

        elif option == '2':
            # Generate grid
            if boundary is None:
                print('You need to load a boundary first.')
                continue
            # Prompt user to select a cell size          
            cell_size = int(input('Enter the cell size in meters: '))
            # Prompt user to select a rotation
            rotation = int(input('Enter the rotation in degrees: '))
            # Prompt user to chooose if he wants to intersect his grid with the polygon boundary
            intersect = input('Do you want to intersect your grid with the boundary? (y/n): ').lower()
            # Promt the user to choose if he wants to clip his grid with boundary
            clip = input('Do you want to clip your grid with the boundary? (y/n): ').lower()
            vector_grid = VectorGrid(boundary, cell_size, rotation, obstacles)
            if intersect=='y':
                vector_grid.intersect()
            if clip=='y':
                vector_grid.clip()
            print(vector_grid.grid.head(100))  
            grid = vector_grid.return_grid()
            vector_grid.visualize()
            # Generate graph
            graph_grid = GraphGrid(grid)
            graph = graph_grid.graph
            print("\n")

        elif option == '3':
            # Generate path
            if graph is None:
                print('You need to generate a grid and a graph first.')
                continue
            print(vector_grid.grid.head(100))
            search_option = input('Do you want to search for the start and end points? (y/n): ')
            if search_option.lower() == 'y':
                start_coordinates = tuple(map(float, input('Enter the UTM coordinates of the start point (separated by a comma): ').split(',')))
                start_id = vector_grid.closest_cell_id(start_coordinates)
                if start_id is None:
                    print("The start point is out of range.")
                    continue
                vector_grid.visualize(start_id)
              
                end_coordinates = tuple(map(float, input('Enter the UTM coordinates of the end point (separated by a comma): ').split(',')))
                end_id = vector_grid.closest_cell_id(end_coordinates)
                if end_id is None:
                    print("The end point is out of range.")
                    continue
                vector_grid.visualize(end_id)           
                input("Press Enter to continue...")
            else:
                while True:
                    start_id = int(input('\n Enter the ID of the start point: '))
                    if start_id not in grid['id'].values:
                        print(f"{Fore.RED}\n Start point {start_id} does not exist. {Style.RESET_ALL}\n")
                        continue
                    elif not grid.loc[grid['id'] == start_id, 'passable'].values[0]:
                        print(f"{Fore.RED}\n Start point {start_id} is not passable.  Select another start point.{Style.RESET_ALL}\n")
                        if len(grid) > 50:
                            print(grid.iloc[max(0, start_id-25):start_id+25])
                        continue
                    else:
                        break
                
                while True:
                    end_id = int(input('Enter the ID of the end point: '))
                    if end_id not in grid['id'].values:
                        print(f"{Fore.RED}\n End point {end_id} does not exist. {Style.RESET_ALL}\n")
                        continue
                    elif not grid.loc[grid['id'] == end_id, 'passable'].values[0]:
                        print(f"{Fore.RED}\n End point {end_id} is not passable. Select another end point.{Style.RESET_ALL}\n")
                        if len(grid) > 50:
                            print(grid.iloc[max(0, end_id-25):end_id+25])
                        continue
                    else:
                        break
                                  
            print(f"Generating path from {start_id} to {end_id}")
            try:
                path = graph_grid.find_path(start_id, end_id)           
                if path is None:
                    print("No path could be found between the start and end points.")
                else:
                    graph_grid.visualize_path()
                    print("\n")
            except ValueError as e:
                print(e)




        elif option == '4':
            # Quit
            break

        else:
            print('Invalid option. Please try again.')

if __name__ == '__main__':
    main()
