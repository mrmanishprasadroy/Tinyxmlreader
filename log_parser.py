import re
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

#
# TlgDefinitinReader
# $Id: TLGDefinitionReader.py  2020-03-31 ROYM $
# use of streamlit app
# use of ElementTree
# use of Plotly
# history:
# 2020-03-31 vl   created
# 2020-04-02 V1.0.01 Added Data type for the Data frame
# 2020-05-17 v1.1.0  Added Decoding of structure in tlg definition
# manish.roy@sms-group.com
# Added File Stream
# --------------------------------------------------------------------
class TinyXmlReader:
    """
    Class to decode tlg structure and passing of the log file
    """

    def __init__(self, filename):
        self.filename = filename
        self.tree = ET.parse(filename)
        self.root = self.tree.getroot()

    def __repr__(self):
        return 'TinyXmlReader({self.root!r})'

    def get_tlg_list(self):
        """
        Extract the Telegrams from the XML file
        :return: telegram list
        """
        tlg_name = []
        for c in self.root.findall('telegram'):
            att = c.attrib
            tlg_name.append(att.get('name'))
        return tlg_name

    def read_sub_list(self, x_string: str) -> list:
        """
              Extract the Record or Element of the telegram from the XML file
              :param x_string: element records search string
              :return: record element list
        """
        return_sub_list = []
        element_sub_list = []
        dsub_type = []
        for item in self.root.findall(x_string):
            # iterate child elements of item
            data_type = ""
            for dt in item.findall("./primitive"):
                sub_att = dt.attrib
                data_type = sub_att.get('appType')
            att = item.attrib
            count = att.get('count')
            counter = int(count)
            dt = data_type
            if counter > 1:
                if re.search(r'\bTime\b', att.get('name'), re.IGNORECASE):
                    element_sub_list.append(att.get('name'))
                    dsub_type.append(np.object)

                else:
                    for idx in range(1, counter + 1):
                        elem = att.get('name') + "_" + str(idx)
                        element_sub_list.append(elem)
                        if dt == 'integer':
                            dsub_type.append('int64')
                        elif dt == 'number':
                            dsub_type.append('float64')
                        else:
                            dsub_type.append('object')
            else:
                element_sub_list.append(att.get('name'))
                if dt == 'integer':
                    dsub_type.append('int64')
                elif dt == 'number':
                    dsub_type.append('float64')
                else:
                    dsub_type.append('object')

        return_sub_list.append(element_sub_list)
        return_sub_list.append(dsub_type)
        return return_sub_list

    def CreateTlgHeader(self, tlg_name: str) -> list:
        """
            Extract the Record or Element of the telegram from the XML file
            :param tlg_name: telegram name
            :return: telegram element list
        """
        return_list = []
        element_list = []
        d_type = []
        sub_element_list = []
        x_string = "./telegram[@name ='" + tlg_name + "']/record/element"
        for item in self.root.findall(x_string):
            # iterate child elements of item
            data_type = ""
            for dt in item.findall("./primitive"):
                sub_att = dt.attrib
                data_type = sub_att.get('appType')
            att = item.attrib
            count = att.get('count')
            kind = att.get('kind')
            counter = int(count)
            dt = data_type
            if not kind:
                x_string = x_string + '/record/element'
                sub_element_list.append(self.read_sub_list(x_string))
            if counter > 1:
                if re.search(r'\bTime\b', att.get('name'), re.IGNORECASE):
                    element_list.append(att.get('name'))
                    d_type.append(np.object)

                else:
                    for idx in range(1, counter + 1):
                        elem = att.get('name') + "_" + str(idx)
                        if not kind:
                            rec_list = sub_element_list[0]
                            for rec_elem in rec_list[0]:
                                element_list.append(rec_elem + "_" + str(idx))
                            for rec_dbtype in rec_list[1]:
                                d_type.append(rec_dbtype)
                        else:
                            element_list.append(elem)
                        if dt == 'integer':
                            d_type.append('int64')
                        elif dt == 'number':
                            d_type.append('float64')
                        else:
                            d_type.append('object')
            else:
                element_list.append(att.get('name'))
                if dt == 'integer':
                    d_type.append('int64')
                elif dt == 'number':
                    d_type.append('float64')
                else:
                    d_type.append('object')

        if element_list.__contains__('Header'):
            element_list.remove('Header')
            del d_type[0]
            element_list.insert(0, 'DateTime')
            d_type.insert(0, 'datetime64[s]')
            element_list.insert(1, 'MessageLength')
            d_type.insert(1, 'int64')
            element_list.insert(2, 'MessageId')
            d_type.insert(2, 'int64')
            element_list.insert(3, 'MessageCount')
            d_type.insert(3, 'int64')
            element_list.insert(4, 'UnitNo')
            d_type.insert(4, 'int64')
        else:
            element_list.insert(0, 'DateTime')
            d_type.insert(0, 'datetime64[s]')

        return_list.append(element_list)
        return_list.append(d_type)
        return return_list

    def make_tlg_value_list(self, sTag: str, file_content: str) -> pd.DataFrame:
        """
        File Processing for extracting the values from Loag file
        :param sTag: Telegram Name
        :param file_content: Logfile name for analysis
        :return: Pandas Data frame
        """
        t_values = []
        return_list = self.CreateTlgHeader(sTag)
        element_list = return_list[0]
        d_types = return_list[1]
        regex = 'TYPE;' + sTag + ';'
        # with open(filename, "r") as file:
        content = file_content.splitlines()
        for line in content:
            if re.search(regex, line, re.IGNORECASE) is not None:
                cLine = line.replace(regex, '')
                datetime = cLine[:23]
                sub_index = cLine.find('BODY')
                tlgValues = cLine.replace(cLine[:sub_index + 5], "")
                values = tlgValues.split('|')
                values.insert(0, datetime)
                tlg_dict = dict(zip(element_list, values))
                t_values.append(tlg_dict)
            # file.close()
        if len(t_values) > 0:
            df = pd.DataFrame(t_values)
            convert_dict = dict(zip(element_list, d_types))
            try:
                df = df.astype(convert_dict)
            except ValueError:
                pass
            return df
