import math

def convert_to_utm(polygon):
    # Determine the UTM zone number for the polygon's centroid
    utm_zone = math.floor((polygon.centroid.x.iloc[0] + 180) / 6) + 1
    # Create a string for the UTM zone's EPSG code
    utm_crs = f'EPSG:326{str(utm_zone).zfill(2)}' if polygon.centroid.y.iloc[0] >= 0 else f'EPSG:327{str(utm_zone).zfill(2)}'
    # Reproject the polygon to the UTM zone
    polygon_utm = polygon.to_crs(utm_crs)
    return polygon_utm