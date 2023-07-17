from typing import Optional, Tuple
import geopandas as gpd
import pyproj
from shapely.geometry import Polygon, box, Point
from shapely.affinity import rotate
from shapely.ops import nearest_points
import math
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from utils import *


class VectorGrid:
    """
    A class used to represent a vector grid.

    Attributes
    ----------
    polygon : gpd.GeoDataFrame
        The polygon to which the grid is applied.
    cell_size : int
        The size of each cell in the grid.
    rotation : Optional[float]
        The rotation of the grid.
    obstacle : Optional[gpd.GeoDataFrame]
        The obstacle within the grid.
    grid : gpd.GeoDataFrame
        The grid itself.

    Methods
    -------
    check_and_convert_crs(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        Checks and converts the CRS of a GeoDataFrame.
    create_vector_grid():
        Creates the vector grid.
    clip():
        Clips the grid with the polygon.
    intersect():
        Intersects the grid with the polygon.
    add_obstacle(obstacle: gpd.GeoDataFrame):
        Adds an obstacle to the grid.
    clear_obstacle():
        Clears the obstacle from the grid.
    visualize(highlight_cell_id: Optional[int] = None):
        Visualizes the grid.
    rotate(rotation: float):
        Rotates the grid.
    return_grid() -> gpd.GeoDataFrame:
        Returns the grid.
    closest_cell_id(utm_coordinates: Tuple[float, float]) -> int:
        Returns the ID of the cell closest to the given UTM coordinates.
    """
    def __init__(self, polygon: gpd.GeoDataFrame, cell_size: int = 50, rotation: Optional[float] = None, obstacle: Optional[gpd.GeoDataFrame] = None):
        self.polygon = self.check_and_convert_crs(polygon)
        self.cell_size = cell_size
        self.rotation = rotation
        self.obstacle = self.check_and_convert_crs(obstacle) if obstacle is not None else None
        self.grid = self.create_vector_grid()

    def check_and_convert_crs(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Checks and converts the CRS of a GeoDataFrame."""
        # Check if the GeoDataFrame's CRS is projected. If not, reproject it to the appropriate UTM zone.
        if not gdf.crs.is_projected:
            # Determine the UTM zone number for the GeoDataFrame's centroid
            utm_zone = math.floor((gdf.centroid.x.iloc[0] + 180) / 6) + 1
            # Create a string for the UTM zone's EPSG code
            utm_crs = f'EPSG:326{str(utm_zone).zfill(2)}' if gdf.centroid.y.iloc[0] >= 0 else f'EPSG:327{str(utm_zone).zfill(2)}'
            # Reproject the GeoDataFrame to the UTM zone
            gdf = gdf.to_crs(utm_crs)
        return gdf

    def create_vector_grid(self):
        """Creates the vector grid."""
        # Calculate the buffer as the maximum distance from the centroid to the polygon's vertices
        buffer = max(self.polygon.centroid.iloc[0].distance(Point(coord)) for coord in self.polygon.geometry.iloc[0].exterior.coords)

        # Get the bounding box of the polygon and apply the buffer
        minx, miny, maxx, maxy = self.polygon.buffer(buffer).bounds.iloc[0]

        # Create the grid
        x_coords = list(range(int(minx), int(maxx), self.cell_size))
        y_coords = list(range(int(miny), int(maxy), self.cell_size))
        grid_polys = []
        for x in x_coords:
            for y in y_coords:
                # Create a polygon for the cell
                cell = box(x, y, x+self.cell_size, y+self.cell_size)
                grid_polys.append(cell)

        # Create a GeoDataFrame
        grid = gpd.GeoDataFrame(grid_polys, columns=['geometry'], crs=self.polygon.crs)  
                
        # Rotate the entire grid
        if self.rotation is not None:
          grid['geometry'] = grid['geometry'].rotate(self.rotation, origin=self.polygon.centroid.iloc[0], use_radians=False)

        # If an obstacle is provided, update the 'passable' attribute of the cells
        if self.obstacle is not None:
            grid['passable'] = ~grid['geometry'].apply(lambda cell: any(cell.intersects(obstacle) for obstacle in self.obstacle.geometry))
        else:
            grid['passable'] = True
        
        # Add an 'id' column
        grid['id'] = range(len(grid))
        return grid

    def clip(self):
        """Clips the grid with the polygon."""
        self.grid = gpd.clip(self.grid, self.polygon)
        # Add an 'id' column
        self.grid['id'] = range(len(self.grid))

    def intersect(self):
        """Intersects the grid with the polygon."""
        self.grid = self.grid[self.grid.intersects(self.polygon.geometry[0])]
        # Add an 'id' column
        self.grid['id'] = range(len(self.grid))

    def add_obstacle(self, obstacle: gpd.GeoDataFrame):
        """Adds an obstacle to the grid."""
        self.obstacle = obstacle
        # Update self.grid to account for the obstacle
        self.grid['passable'] = ~self.grid['geometry'].apply(lambda cell: any(cell.intersects(obstacle) for obstacle in self.obstacle.geometry))

    def clear_obstacle(self):
        """Clears the obstacle from the grid."""
        self.obstacle = None
        # Update self.grid to remove the obstacle
        self.grid['passable'] = True

    def visualize(self, highlight_cell_id: Optional[int] = None):
        """Visualizes the grid."""
        fig, ax = plt.subplots()
        if self.grid['passable'].any():  # If there are any passable cells
            self.grid[self.grid['passable']].plot(ax=ax, color='green', edgecolor='black')
        if (~self.grid['passable']).any():  # If there are any impassable cells
            self.grid[~self.grid['passable']].plot(ax=ax, color='red', edgecolor='black')
        if highlight_cell_id is not None:  # If a cell ID is provided to highlight
            self.grid[self.grid['id'] == highlight_cell_id].plot(ax=ax, color='gold', edgecolor='black')
        self.polygon.boundary.plot(ax=ax, color='violet')
        legend_elements = [Patch(facecolor='green', edgecolor='black', label='Passable'),
                           Patch(facecolor='red', edgecolor='black', label='Impassable'),
                           Patch(facecolor='gold', edgecolor='black', label='Highlighted')]
        ax.legend(handles=legend_elements, loc='upper right')
        plt.title('Vector Grid')
        plt.xlabel('Easting (m)')
        plt.ylabel('Northing (m)')
        plt.show()

    def rotate(self, rotation: float):
        """Rotates the grid."""
        self.rotation = rotation
        # Update self.grid to account for the new rotation
        self.grid['geometry'] = self.grid['geometry'].rotate(self.rotation, origin=self.polygon.centroid.iloc[0], use_radians=False)

    def return_grid(self) -> gpd.GeoDataFrame:
        """Returns the grid."""
        return self.grid

    def closest_cell_id(self, utm_coordinates: Tuple[float, float]) -> int:
        """Returns the ID of the passable cell closest to the given UTM coordinates."""
        # Create a Point from the UTM coordinates
        point = Point(utm_coordinates)
    
        # Create a MultiPoint object from the centroids of all passable cells
        multipoint = self.grid[self.grid['passable']]['geometry'].centroid.unary_union
    
        # Find the nearest point in the MultiPoint object to the given point
        nearest = nearest_points(point, multipoint)[1]
    
        # Find the cell whose centroid is the nearest point
        closest_cell_id = self.grid[self.grid['geometry'].centroid == nearest]['id'].values[0]
    
        return closest_cell_id

# Tests
# Enter the UTM coordinates of the start point (separated by a comma): 5133699,4645005
# Enter the UTM coordinates of the end point (separated by a comma): 512815,4645502
# #Load geojson 
# polygon = gpd.read_file('data/demo_boundary.geojson')
# polygon = convert_to_utm(polygon)

# obstacles = gpd.read_file('data/obstacles.geojson')
# obstacles = convert_to_utm(obstacles)

# vg = VectorGrid(polygon=polygon, cell_size=25, obstacle=obstacles)
# vg.intersect()
# #vg.visualize()

# print("1")
# cell = vg.closest_cell_id((513012,4645351))
# print(cell)
# print("2")
# vg.visualize(highlight_cell_id=cell)
