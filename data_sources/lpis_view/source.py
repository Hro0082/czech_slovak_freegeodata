from .. source import Source
import os
from qgis.core import *
from qgis.PyQt.QtCore import QVariant
import xml.etree.ElementTree as ET
from zipfile import ZipFile
import urllib3
import tempfile
import csv
import math
from .options_dialog import OptionsDialog

class Lpis(Source):

    def get_vector(self, extent, EPSG):
        katuzid = self.get_katuzid(extent, EPSG)
        path = self.download_from_lpis(katuzid)
        if path is None:
            QgsMessageLog.logMessage("File for " + katuzid + " was not downloaded", "GeoData")
            return None
        else:
            vector = self.create_vector(path, katuzid)
            vector.loadNamedStyle(os.path.dirname(__file__) + '/data/style.qml')
            if not vector.isValid():
                QgsMessageLog.logMessage("Layer " + path + " was not loaded", "GeoData")
                return None
            else:
                return vector

    def get_raster(self, extent, EPSG):
        return None

    def get_xy_center(self, extent, EPSG):
        print(extent)
        print(EPSG)
        if EPSG == "EPSG:5514":
            return [extent.center().x(), extent.center().y()]
        else:
            crs_dest = QgsCoordinateReferenceSystem(5514)
            crs_src = QgsCoordinateReferenceSystem(int(EPSG.split(":")[1]))
            xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
            extent_5514 = xform.transform(extent)
            return [extent_5514.center().x(), extent_5514.center().y()]
        # return [-735295, -1105580]

    def get_katuzid(self, extent, EPSG):
        # TODO search for katuzid
        # We will simply search for just one katuz that is in the center of the map
        xy = self.get_xy_center(extent, EPSG)
        current_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(current_dir, 'data', 'katuz.csv')
        mindistance = float('inf')
        katuzid = None
        with open(path, "r") as f:
            katuzreader = csv.reader(f, delimiter=';')
            for row in katuzreader:
                distance = math.hypot(abs(int(row[1]) - xy[0]), abs(int(row[2]) - xy[1]))
                if distance < mindistance:
                    mindistance = distance
                    katuzid = row[0]
        print(katuzid)
        return katuzid
        # return "798428"

    def download_from_lpis(self, katuzid):
        # TODO download from LPIS and unzip XML file
        # http://eagri.cz/public/app/eagriapp/lpisdata/20200801-798428-DPB-XML-A.zip
        # TODO get current month
        last_date = "20200801"
        url = "http://eagri.cz/public/app/eagriapp/lpisdata/" + last_date + "-" + katuzid + "-DPB-XML-A.zip"
        http = urllib3.PoolManager()
        response = http.request('GET', url, preload_content=False)
        content_length = response.headers['Content-Length']
        total_size = int(content_length) # TODO maybe return progress later
        downloaded = 0
        CHUNK = 256 * 10240
        zip_temp = tempfile.NamedTemporaryFile(mode='w+b', suffix='.zip', delete=False)
        zip_temp_n = zip_temp.name
        zip_temp.seek(0)

        with open(zip_temp_n, 'wb') as fp:
            while True:
                chunk = response.read(CHUNK)
                downloaded += len(chunk)
                if not chunk:
                    break
                fp.write(chunk)
        response.release_conn()

        lpis_zip = ZipFile(zip_temp)
        current_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        lpis_zip.extractall(os.path.join(current_dir, 'data'))
        zip_temp.close()

        current_file = None
        for name in os.listdir(os.path.join(current_dir, 'data')):
            if katuzid in name:
                current_file = os.path.join(current_dir, 'data', name)
        return current_file

    def create_vector(self, path, katuzid):
        # create layer
        vl = QgsVectorLayer("Polygon", "LPIS " + katuzid, "memory")
        pr = vl.dataProvider()
        pr.addAttributes([QgsField("kultura", QVariant.String)])
        vl.updateFields()

        tree = ET.parse(path)
        root = tree.getroot()
        ns = {'ns2': 'http://sitewell.cz/lpis/schemas/LPI_GDP01A'}
        for dpb in root.findall('.//ns2:DPB', ns):
            # add a feature
            fet = QgsFeature()
            for geometry in dpb.findall('.//ns2:GEOMETRIE', ns):
                fet.setGeometry(QgsGeometry.fromWkt(geometry.text))
            for kultura in dpb.findall('.//ns2:KULTURANAZEV', ns):
                fet.setAttributes([kultura.text])
            pr.addFeatures([fet])
            vl.updateExtents()

        return vl

    def has_options_dialog(self):
        return True

    def show_options_dialog(self):
        self.dlg = OptionsDialog()
        self.dlg.show()
