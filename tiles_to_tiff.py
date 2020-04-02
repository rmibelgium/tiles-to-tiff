import math
import urllib.request
import os
import glob
import subprocess
import shutil
from tile_convert import bbox_to_xyz, tile_edges
from osgeo import gdal

#---------- CONFIGURATION -----------#
tile_server = "https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}.png?access_token=" + os.environ.get(
    'MAPBOX_ACCESS_TOKEN')
temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
output_dir = os.path.join(os.path.dirname(__file__), 'output')
zoom = 16
lon_min = 21.49147
lon_max = 21.5
lat_min = 65.31016
lat_max = 65.31688
#-----------------------------------#


def download_tile(x, y, z, tile_server):
    url = tile_server.replace(
        "{x}", str(x)).replace(
        "{y}", str(y)).replace(
        "{z}", str(z))
    path = f'{temp_dir}/{x}_{y}_{z}.png'
    urllib.request.urlretrieve(url, path)
    return(path)


def merge_tiles(temp_dir, output_dir):
    merge_command = ['gdalbuildvrt', temp_dir + '/merged.vrt']
    input_pattern = temp_dir + '/*.tif'

    for name in glob.glob(input_pattern):
        subprocess.call(["pct2rgb.py", name, name + '.rgb.tif'])
        merge_command.append(name + '.rgb.tif')

    subprocess.call(merge_command)
    subprocess.call(["echo", "gdal_translate", temp_dir + "/merged.vrt", output_dir + "/merged.tif"])
    subprocess.call(["echo", "gdal_translate", temp_dir + "/merged.vrt", output_dir + "/merged.png"])


def georeference_raster_tile(x, y, z, path):
    bounds = tile_edges(x, y, z)
    filename, extension = os.path.splitext(path)
    gdal.Translate(filename + '.tif',
                   path,
                   outputSRS='EPSG:4326',
                   outputBounds=bounds)


x_min, x_max, y_min, y_max = bbox_to_xyz(
    lon_min, lon_max, lat_min, lat_max, zoom)

print(f"Downloading {(x_max - x_min + 1) * (y_max - y_min + 1)} tiles")

for x in range(x_min, x_max + 1):
    for y in range(y_min, y_max + 1):
        print(f"{x},{y}")
        png_path = download_tile(x, y, zoom, tile_server)
        georeference_raster_tile(x, y, zoom, png_path)

print("Download complete")

print("Merging tiles")
merge_tiles(temp_dir, output_dir)
print("Merge complete")

shutil.rmtree(temp_dir)
os.makedirs(temp_dir)
