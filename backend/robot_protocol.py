import json, os

from deck_module import DeckModule
from file_io import FileIO


debug = True

class RobotProtocol:
	"""Port of createJobFile.js into python, start of move to a new framework.
		1st move createJobFile into python
		2nd piece by piece replace it with pieces from new framework"""

	def __init__(self, protocol, containers):
		# 1. create representation of wells (coordinates & current volume)
		self.protocol = dict()
		self.labware_from_db = dict()
		if isinstance(protocol, dict):
			self.protocol = protocol
		if isinstance(containers, dict):
			self.labware_from_db = containers

		self._deck = dict()

		for variableName, variableValue in self.protocol.deck.items():
			_container = dict()
			labwareName = variableValue.labware
			_container['labware'] = labwareName
		
			if len(list(labwware_from_db))>0 && labwareName in list(labware_from_db):
				_container['locations'] = labware_from_db[labwareName]['locations']
		
				if 'locations' in list(_container):
					for locationName, locationValue in _container['locations'].items():
						currentLocation = locationValue
						if 'total-liquid-volume' in list(currentLocation):
							self.createLiquidLocation(currentLocation)
			else:
				file_io.log('"',labwareName,'" not found in labware definitions')

			self._deck[variableName] = _container

		#2. Now add the starting ingredients to those created locations (wells)

		for ingredientName, ingredientValue in self.protocol.ingredients.items():
			ingredientPartsList = ingredientValue
			map(lambda self, ingredientPart: self.ingredientPartUpdate(ingredientPart),ingredientPartsList)

		
		#3. Give the pipettes access to the deck, so they can do .pickupTip() and .dropTip()

		self._pipettes = dict()

		for toolName, toolValue in protocol.head.items():
			self._pipettes[toolName] = toolValue
			self._pipettes['tip-rack-objs'] = dict()
			self._pipettes['trash-container-objs'] = dict()
			self._pipettes['current-plunger'] = 0

			self._pipettes['down-plunger-speed'] = 300
			self._pipettes['up-plunger-speed'] = 0
			self._pipettes['distribute-percentage'] = 0

			if 'down-plunger-speed' in list(toolValue):
				if isinstance(toolValue['down-plunger-speed'],(int,float,complex)):
					self._pipettes['down-plunger-speed'] = toolValue['down-plunger-speed']
			if 'up-plunger-speed' in list(toolValue):
				if isinstance(toolValue['up-plunger-speed'],(int,float,complex)):
					self._pipettes['up-plunger-speed'] = toolValue['up-plunger-speed']
			if 'distribute-percentage' in list(toolValue):
				if toolValue['distribute-percentage'] < 0:
					self._pipettes['distribute-percentage'] = 0
				if toolValue['distribute-percentage'] > 1:
					self._pipettes['distribute-percentage'] = 1
			if 'points' in list(toolValue):
				self._pipettes['points'].sort(key=lambda a,b: a.f1-b.f1)

			_trashcontainerName = ""

			if isinstance(self.pipettes['trash-container']):
				_trashcontainerName = self._pipettes[toolName]['trash-container'][0].strip()
			else:
				_trashcontainerName = self._pipettes[toolName].container.strip()
			if len(_trashcontainerName)>0 and _trashcontainerName in list(self._deck):
				trashLabware = self._deck[_trashcontainerName].labware
				if trashLabware is not None:
					self._pipettes[toolName]['trash-container-objs'][_trashcontainerName] = dict()
					self._pipettes[toolName]['trash-container-objs'][_trashcontainerName]['locations'] = self.containers[trashLabware].locations
			else:
				file_io.log('"',_trashcontainerName,'" not found in deck')

			_tr_list = list()
			_tr_list = self._pipettes[toolName]['tip-racks']
			_tr_objs = dict()
			if len(_tr_list) > 0:
				for _rack in _tr_list:
					containerName = ""
					if isinstance(_tr_list[_rack],str):
						containerName = _tr_list[_rack].strip()
					else:
						containerName = _tr_list[_rack].container.strip()
					_tr_objs[containerName] = dict()
					_tr_objs[containerName]['container'] = containerName
					_tr_objs[containerName]['clean-tips'] = list()
					_tr_objs[containerName]['dirty-tips'] = list()

					labwareName = self._deck[containerName].labware.strip()

					if labwareName in self.labware_from_db:
						_locations = labware_from_db[labwareName].locations
						for locName in list(_locations):
							_tr_objs[containerName]['clean-tips'].append(_locations[locName])
					else:
						file_io.log('"',labwareName,'" not found in labware definitions')
				self._pipettes[toolName]['tip-rack-objs'] = _tr_objs
				self._pipettes[toolName]['pickupTip'] = lambda self: self._pickupTip(self.pipette)
				self._pipettes[toolName]['dropTip'] = lambda self: self._dropTip(self.pipette)

		#4. Make array of instructions, to hold commands and their individual move locations

		self.createdInstructions = list()

		self._instructions = protocol.instructions

		for toolname in self._pipettes:
			ci = dict(
				{
					'tool' : self._pipettes[toolname].tool,
					'groups' : [
						{
							'command':'pipette',
							'axis':self._pipettes[toolname].axis,
							'locations': [
								{
									'plunger':'blowout'
								},
								{
									'plunger':'resting'
								},
								{
									'plunger':'blowout'
								},
								{
									'plunger':'resting'
								}
							]
						}
					]
				}
				)
				
			self.createdInstructions.append(ci)

			for i in self._instructions:
				currentPipette = self._pipettes[self._instructions[i].tool]

				if currentPipette is not None:
					newInstruction = dict()
					newInstruction['tool'] = currentPipette.tool
					newInstruction['groups'] = list()

					for g in self._instructions[i].groups:
						newGroup = None
						if 'transfer' in list(g):
							newGroup = self.transfer(self._deck, pipette, g['transfer'])
						elif 'distribute' in list(g):
							newGroup = self.distribute(self._deck, pipette, g['distribute'])
						elif 'consolidate' in list(g):
							newGroup = self.consolidate(self._deck, pipette, g['consolidate'])
						elif 'mix' in list(g):
							newGroup = self.mix(self._deck, pipette, g['mix'])

						if newGroup is not None:
							newInstruction['groups'].append(newGroup)


		return self.createdInstructions


	def createLiquidLocation(self, location):
		location['current-liquid-volume'] = 0
		location['current-liquid-offset'] = 0
		location['updateVolume'] = lambda self, location, ingredientVolume: self.updateVolume(location, ingredientVolume)


	def updateVolume(self, location, ingredientVolume):
		"""turned into lambda for location dict"""
		location['current-liquid-volume'] += ingredientVolume
		heightRatio = location['current-liquid-volume'] / location['total-liquid-volume']
		if isinstance(heightRatio,(int,float,complex)):
			location['current-liquid-volume'] = location['depth'] - (location['depth'] * heightRatio)


	def ingredientPartUpdate(self, ingredientPart):
		if 'container' in list(ingredientPart) and ingredientPart['container'] in list(self._deck):
			allLocations = self._deck[ingredientPart.container].locations
				if 'location' in list(ingredientPart) and ingredientPart.location in list(allLocations):
					currentLocation = allLocations[ingredientPart.location]
					ingredientVolume = ingredientPart.volume

					if isinstance(ingredientVolume, (int, float, complex)) and 'updateVolume' in list(currentLocation):
						currentLocation.updateVolume(currentLocation, ingredientVolume)


	def _pickupTip(self, pipette):
		myRacks = pipette['tip-rack-objs']
		pipette.justPickedUp = True

		newTipLocation = None
		newTipContainerName = None

		for rackName, rackValue in myRacks.items():
			if len(rackValue['clean-tips']>0):
				howManyTips = pipette['multi-channel'] ? 8 : 1 # <---- ????
				if not isinstance(howManyTips,int):
					howManyTips = 1
				newTipLocation = rackValue['clean-tips'] #.splice(0,1)[0]
				newTipContainerName = ""
				newTipContainerName = rackValue.container
				rackValue['dirty-tips'].append(newTipLocation)
				for n in range(howManyTips-1):
					tempTip = rackValue['clean-tips'] #.splice(0,1)[0]
					if tempTip is not None:
						rackValue['dirty-tips'].append(tempTip)

		if newTipLocation is not None:
			for rackName, rackValue in myRacks.items():
				rackValue['clean-tips'] = rackValue['dirty-tips']
				rackValue['dirty-tips'] = []

			if len(list(myRacks)) > 0:
				newTipLocation = myRacks[myRacks.keys()[0]]['clean-tips'] #.splice(0,1)[0]
				newTipContainerName = myRacks[myRacks.keys()[0]].container
				myRacks[myRacks.keys()[0]]['dirty-tips'].append(newTipLocation)

		moveList = list()

		movie = dict({'z':0})
		moveList.append(movie)
		
		pipette['current-plunger'] = 0
		
		movie = dict({'plunger':'resting'})
		moveList.append(movie)

		movie = dict({'x':newTipLocaiton.x,'y':newTipLocation.y,'container':newTipContainerName})
		moveList.append(movie)

		for i in range(3):
			movie = dict({'z':newTipLocation.z-pipette['tip-plunge'],'container':newTipContainerName})
			moveList.append(movie)

			movie = dict({'z':newTipLocation.z+1,'container':newTipContainerName})
			moveList.append(movie)

		return moveList


	def _dropTip(self, pipette):
		moveList = list()
		trashContainerName = ""

		if isinstance(pipette['trash-container']):
			trashContainerName = pipette['trash-container'][0]
		else
			trashContainerName = pipette['trash-container'].container

		trashLocation = None
		for o,v in pipette['trash-container-objs'][trashContainerName].locations.items():
			trashLocation = v

		movie = dict({'z':0})
		moveList.append(movie)

		pipette['current-plunger'] = 0

		movie = dict({'plunger':'resting'})
		moveList.append(movie)

		movie = dict({'x':trashLocation.x,'y':trashLocation.y,'container':trashContainerName})
		moveList.append(movie)

		movie = dict({'z':trashContainer.z,'container':trashContainerName})
		moveList.append(movie)

		movie = dict({'plunger':'droptip'})
		moveList.append(movie)

		return moveList





	def createPipetteGroup(self, type, theDeck, theTool, trasnferList):



	def transfer(self, theDeck, theTool, transferList):
		createdGroup = dict({
			'command':'pipette',
			'axis':theTool.axis,
			'locations':list()
			})
		pickupList = theTool.pickupTip()
		createdGroup.locations.append(pickupList)

		for i in transferList:
			thisTransferParams = i
			fromParams = thisTransferParams['from']
			toParams = thisTransferParams['to']
			volume = thisTransferParams['volume']

			fromParams['volume'] = volume * -1
			toParams['volume'] = volume

			fromParams['extra-pull'] = thisTransferParams['extra-pull']

			fromList = self.makePipettingMotion(theDeck, theTool, fromParams, True)
			createdGroup.locations.append(fromList) #replaces _addMovements(fromArray)

			toList = self.makePipettingMotion(theDeck, theTool, toParams, False)
			createdGroup.locations.append(toList)

		dropList = theTool.dropTip()
		createdGroup.locations.append(dropList)

		return createdGroup

	def distribute(self, theDeck, theTool, distributeGroup):
		createdGroup = dict({
				'command':'pipette',
				'axis':theTool.axis,
				'locations':list()
			})
		pickupList = theTool.pickupTip()
		createdGroup.locations.append(pickupList)

		toParamsList = distributeGroup['to']
		totalPercentage = 0
		for i in list(toParamsList):
			totalPercentage += getPercentage(i.volume,theTool)
		totalVolume = theTool.volume * totalPercentage
		totalVolume += totalVolume * theTool['distribute-percentage']
		if totalVolume > theTool.volume:
			totalVolume = float(theTool.volume)



	def consolidate(self, theDeck, theTool, consolidateGroup):
		createdGroup = dict({
				'command':'pipette',
				'axis':theTool.axis,
				'locations':list()
			})
		pickupList = theTool.pickupTip()
		createdGroup.locations.append(pickupList)

		fromParamsList = consolidatedGroup['from']
		totalPercentage = 0

		for i in list(fromParamsList):
			fromParams = i
			totalPercentage += getPercentage(fromParams.volume, theTool)
			fromParams.volume *= -1
			fromParams['extra-pull'] = consolidateGroup['extra-pull']

			tempFromList = self.makePipettingMotion(theDeck, theTool, fromParams, i===0)
			createdGroup.locations.append(tempFromList)

		totalVolume = totalPercentage * theTool.volume

		toParams = consolidatedGroup['to']
		toParams.volume = totalVolume

		tempToArray = self.makePipettingMotion(theDeck, theTool, toParams, False)
		createdGroup.locations.append(tempToArray)

		return createdGroup


	def mix(self, theDeck, theTool, mixListOfDicts):
		createdGroup = dict({
				'command':'pipette',
				'axis':theTool.axis,
				'locations':list()
			})

		pickupList = theTool.pickupTip()
		createdGroup.locations.append(pickupList)

		for i in list(mixListOfDicts):
			thisParam = i
			thisParam.volume *= -1
			mixMoveCommands = self.makePipettingMotion(theDeck, theTool, thisParam, True)
			createdGroup.locations.append(mixMoveCommands)

		dropList = theTool.dropTip()
		createdGroup.locations.append(dropList)

		return createdGroup


	def makePipettingMotion(self, theDeck, theTool, thisParams, shouldDropPlunger):
		moveList = list()
		containerName = thisParams.container
		if containerName in list(theDeck) and 'locations' in list(theDeck[containerName]):
			locationPos = theDeck[containerName].locations[thisParams.location]

			locationPos.updateVolume(float(thisParams.volume))
			specifiedOffset = thisParams['tip-offset'] || 0
			arriveDepth = 0
			bottomLimit = (locationPos.depth - 0.2) * -1

			if thisParams['liquid-tracking'] === True:
				arriveDepth = specifiedOffset-locationPos['current-liquid-offset']
			else:
				arriveDepth = bottomLimit + specifiedOffset

			if arriveDepth < bottomLimit:
				arriveDepth = bottomLimit

			moveList.append(dict({'speed':theTool['down-plunger-seed']}))

			rainbowHeight = highestSpot - 5

			if theTool.justPickedUp === True:
				rainbowHeight = 0
				theTool.justPickedUp = False

			moveList.append(dict({'z':rainbowHeight}))

			if shouldDropPlunger === True:
				theTool['current-plunger'] = 0
				moveList.append(dict({'plunger':'resting'}))
				moveList.append(dict({
						'x':locationPos.x,
						'y':locationPos.y,
						'container':containerName
					}))
				moveList.append(dict({
						'z':1
						'container':containerName
					}))

			if shouldDropPlunger === True:
				theTool['current-plunger'] = 0.1
				moveList.append(dict({
						'plunger':theTool['current-plunger']
					}))
				theTool['current-plunger'] = 0.95
				moveList.append(dict({
						'plunger':theTool['current-plunger']
					}))
			
			moveList.append(dict({
						'z':arriveDepth,
						'container':containerName
					}))
			if shouldDropPlunger === True:
				theTool['current-plunger'] = 1
				moveList.append(dict({
						'plunger':theTool['current-plunger']
					}))
			if not isinstance(thisParams['delay'],(int,float,complex)):
				moveList.append(dict({
						'delay':thisParams['delay']
					}))
			
			plungerPercentage = self.getPercentage(thisParams.volume, theTool)
			extraPercentage = 0

			if 'repetitions' in list(thisParams):
				locationPos.updateVolume(float(thisParams.volume * -1))

				for i in range(float(thisParams.repititions)):
					moveList.append(dict({
							'speed':theTool['up-plunger-speed']
						}))
					theTool['current-plunger']+=plungerPercentage
					moveList.append(dict({
							'plunger':theTool['current-plunger']
						}))
					moveList.append(dict({
							'speed':theTool['down-plunger-speed']
						}))
					theTool['current-plunger']-=plungerPercentage
					moveList.append(dict({
						'plunger':theTool['current-plunger']
						}))
			else:
				if shouldDropPlunger===True and 'extra-pull-volume' in list(theTool) and 'extra-pull' in list(thisParams):
					extraPercentage = (float(theTool['extra-pull-volume'])/theTool.volume)

				moveList.append(dict({
						'speed':theTool['up-plunger-speed']
					}))

				theTool['current-plunger']+=(plungerPercentage - extraPercentage)
				if theTool['current-plunger']<0:
					theTool['current-plunger'] = 0
				moveList.append(dict({
						'plunger':theTool['current-plunger']
					}))
				if extraPercentage!==0:
					delayTime = 200
					if not isinstance(theTool['extra-pull-delay']):
						delayTime = abs(theTool['extra-pull-delay'])

					moveList.append(dict({'delay':delaytime}))

					moveList.append(dict({'speed':theTool['down-plunger-speed']}))

					theTool['current-plunger'] += extraPercentage
					moveList.append(dict({'plunger':theTool['current-plunger']}))

				if not isinstance(theTool['delay'],(int,float,complex)):
					moveList.append(dict({'delay':thisParams['delay']}))

				moveList.append(dict({'speed':theTool['down-plunger-speed']}))

				moveList.append(dict({
					'z':0,
					'container':containerName
					}))

				if 'blowout' in list(thisParams):
					moveList.append(dict({'plunger':'blowout'}))

				if 'touch-tip' in list(thisParams) and 'diameter' in list(locationPos):
					moveList.append(dict({
							'y':locationPos['diameter'] / 2,
							'relative':True
						}))
					moveList.append(dict({
							'y':-locationPos['diameter'],
							'relative':True
						}))
					moveList.append(dict({
							'y':location['diameter'] / 2,
							'relative':True
						}))
					moveList.append(dict({
							'x':locationPos['diameter'] / 2,
							'relative':True
						}))
					moveList.append(dict({
							'x':-locationPos['diameter'],
							'relative':True
						}))
					moveList.append(dict({
							'x':locationPos['diameter'] / 2,
							'relative':True
						}))

		return moveList

	def getPercentage(self, thisVolume, theTool):
		realVolume = float(thisVolume)
		absVolume = abs(realVolume)

		amountToScale = 1

		if absVolume is not None and theTool is not None and 'points' in list(theTool):
			for i in range(len(theTool.points)-1):
				if absVolume >= theTool.points[i].f1 and absVolume <= theTool.points[i+1].f1:
					f1Diff = theTool.points[i+1].f1 - theTool.points[i].f1
					f1Percentage = (absVolume - theTool.points[i].f1) / f1Diff
					lowerScale = theTool.points[i].f1 / theTool.points[i].f2
					upperScale = theTool.points[i+1].f1 / theTool.points[i+1].f2

					amountToScale = ((upperScale - lowerScale) * f1Percentage) + lowerScale

					break

		absVolume *= amountToScale
		if realVolume < 0:
			absVolume *= -1

		return absVolume / theTool.volume








