import json, os, collections

from deck_module import DeckModule
from file_io import FileIO


debug = True
verbose = False

class Deck:
    """The Deck class is a representation of the robot deck

    The Deck class is intended to be instantiated to a deck object which 
    contains the subclassed deck modules labeled by slot #.
    Slot numbers are integers from 1 to 15, starting from the front-left slot
    and ending with the back-right slot as follows:
    
    +--+--+--+--+--+
    |  |  |  |  |  |
    | 3| 6| 9|12|15|
    +--+--+--+--+--+
    |  |  |  |  |  |
    | 2| 5| 8|11|14|
    +--+--+--+--+--+
    |  |  |  |  |  |
    | 1| 4| 7|10|13|
    +--+--+--+--+--+
    """
#Special Methods
    def __init__(self, modules, publisher, containers):
        """Initialize the Deck
        
        modules = a dictionary of the modules needed on the deck of the form:

            "p200-rack" : {"labware" : "tiprack-200ul","slot" : 1},
            "p200-rack-2" : {"labware" : "tiprack-200ul","slot" : 6},
            "p1000-rack" : {"labware" : "tiprack-1000ul","slot" : 7},
            "plate-1": {"labware": "96-flat", "slot" : 11},
            "plate-2": {"labware": "96-flat", "slot" : 8},
            "trash": {"labware": "point", "slot" : 12}
        """
        if debug == True: FileIO.log('deck.__init__ called')
        self.modules = modules
        self.pubber = publisher
        self.containers = containers
        self.path = os.path.abspath(__file__)
        self.dir_path = os.path.dirname(self.path)  
        self.dir_par_path = os.path.dirname(self.dir_path)
        self.dir_par_par_path = os.path.dirname(self.dir_par_path)  
        
        
    def __str__(self):
        return "Deck"
       
       
    def __repr__(self):
        return "Deck({0!r})".format(self.modules.keys())
    
    
#Methods
    def configure_deck(self, deck_data):
        """Load deck modules specified in protocol.json file
        
        deck_data = dictionary containing the module data.
        :returns: A list of instantiated deck modules
        :rtype: List
        """
        if debug == True: FileIO.log('deck.configure_deck called')
        #delete any previous deck configuration
        del self.modules
        self.modules = []
        
        #instantiate a new deck module for each name in the file
        #ToDo - check for data validity before using
        for key in deck_data:
            dd = deck_data[key]
            if 'slot' in dd:
                newmod = DeckModule(key,dd['labware'],dd['slot'])
            else:
                newmod = DeckModule(key,dd['labware'],0)
            self.modules.append(newmod)
            
        return self.modules


    def save_containers(self, containers_data):
        if debug == True: FileIO.log('deck.save_containers called')
        containers_text = json.dumps(containers_data,sort_keys=True,indent=4,separators=(',',': '))
        if debug == True: FileIO.log('containers_text: ', containers_text)
        filename = os.path.join(self.dir_par_par_path,'otone_data/containers.json')
        FileIO.writeFile(filename,container_text,lambda: FileIO.onError('\t\tError saving the file:\r\r'))              


    def get_containers(self):
        if debug == True: FileIO.log('deck.get_containers called')
        #containers_old = FileIO.get_dict_from_json(os.path.join(self.dir_par_par_path,'otone_data/containers.json'))
        #return containers_old
        new_containers = dict({'containers':dict()})
        
        for c in self.containers.list_containers():
            try:
                temp_container = dict()
                temp_container = json.loads(self.containers.generate_legacy_container(c,True),object_pairs_hook=collections.OrderedDict)
                list(temp_container)[0].replace('legacy.','')
                new_containers['containers'].update(temp_container)
            except KeyError:
                temp_container = dict()
                temp_container = json.loads(self.containers.generate_legacy_container('legacy.'+c,True),object_pairs_hook=collections.OrderedDict)
                list(temp_container)[0].replace('legacy.','')
                new_containers['containers'].update(temp_container)
        FileIO.log('new_containers: ')
        FileIO.log(new_containers)
        return new_containers
                

    def publish_containers(self):
        if debug == True: FileIO.log('deck.publish_containers called')
        self.pubber.send_message('containers',self.get_containers())


    def container_depth_override(self, container_name, new_depth):
        FileIO.log('deck.container_depth_override called')
        containers = FileIO.get_dict_from_json(os.path.join(self.dir_par_par_path,'otone_data/containers.json'))
        if container_name in containers and new_depth is not None:
            if 'locations' in containers[container_name]:
                containers[container_name]['locations']['depth'] = new_depth
                self.save_containers(containers)
                self.publish_containers()
            else:
                FileIO.log('error in deck.container_depth_override, locations not in containers-->',container_name)

