import pyomo.environ as pyomo       # Used to model the IP
import readAndWriteJson as rwJson   # Used for reading the data file in Json format
import matplotlib.pyplot as plt     # Used for plotting the result
import time as tm                   # Used for timing the solution process


def readData(filename: str) -> dict:
    data = rwJson.readJsonFileToDictionary(filename)
    return data


def checkFeasibility(model: pyomo.ConcreteModel()) -> list:
    nodeVisited = [False]*model.numOfNodes
    cutList = []
    nodeVisited[0] = True
    printPartialSolutionToScreen = False

    for idx, node in enumerate(nodeVisited):
        if not node:
            # Find sub-tour including node
            currentNode = idx
            # Add empty cut to list of cuts
            cutList.append([idx])
            # Find first on tour
            for j in model.nodes:
                if pyomo.value(model.x[currentNode, j]) >= 0.9999:
                    if printPartialSolutionToScreen:
                        print('0 ->', j, end='')
                    currentNode = j
                    cutList[-1].append(j)
                    nodeVisited[currentNode] = True
                    break
            # Find the rest of the nodes on the (sub) tour
            while currentNode != idx:
                # Find the next node
                for j in model.nodes:
                    if pyomo.value(model.x[currentNode, j]) >= 0.9999:
                        if printPartialSolutionToScreen:
                            print('->', j, end='')
                        currentNode = j
                        if currentNode != idx:
                            cutList[-1].append(j)
                        nodeVisited[currentNode] = True
                        break
            if printPartialSolutionToScreen:
                print('')
    return cutList


def addCut(cutList: list, model: pyomo.ConcreteModel()):
    for cut in cutList:
        model.SECs.add(expr=sum(model.x[i, j] for i in cut for j in cut if i != j) <= len(cut) - 1)


def buildModel(data: dict) -> pyomo.ConcreteModel():
    model = pyomo.ConcreteModel()
    model.numOfNodes = data['n']+1
    # Add descriptive comments here
    model.nodes = range(0, model.numOfNodes)
    model.x = pyomo.Var(model.nodes, model.nodes, within=pyomo.Binary)
    # Add descriptive comments here
    for i in model.nodes:
        model.x[i, i].fix(0)
    # Add descriptive comments here
    model.obj = pyomo.Objective(
        expr=sum(data['dist'][i][j]*model.x[i, j] for i in model.nodes for j in model.nodes if i != j)
    )
    # Add descriptive comments here
    model.sumToOne = pyomo.ConstraintList()
    for i in model.nodes:
        # Out of node i
        model.sumToOne.add(expr=sum(model.x[i, j] for j in model.nodes if i != j) == 1)
        # Into node i
        model.sumToOne.add(expr=sum(model.x[j, i] for j in model.nodes if i != j) == 1)
    model.SECs = pyomo.ConstraintList()
    return model


def solveModel(model: pyomo.ConcreteModel()):
    solver = pyomo.SolverFactory('gurobi')
    cutsAdded = 0
    iterations = 0
    forPrint = ['Iterations', 'Cuts added', 'Objective value']
    print("{: >10} {: >15} {: >20}".format(*forPrint))
    start_time = tm.time()
    while True:
        solver.solve(model, tee=False)
        cutList = checkFeasibility(model)
        optValue = pyomo.value(model.obj)

        if len(cutList[0]) == model.numOfNodes:
            break
        else:
            cutsAdded += len(cutList)
            addCut(cutList, model)
        iterations += 1
        forPrint = [iterations, cutsAdded, optValue]
        print("{: >10} {: >15} {: >20.4f}".format(*forPrint))
    print("Solution process took %.6s seconds" % (tm.time() - start_time))
    print('Number of cuts added before optimal solution was proven:', cutsAdded)


def displaySolution(model: pyomo.ConcreteModel(), data: dict):
    print('Solution value is:', pyomo.value(model.obj))
    # Print solution information to prompt
    print('Objective function value =', pyomo.value(model.obj))
    print('Optimal tour is')
    curNode = 0
    print(curNode, '->', end='')
    KeepOn = True
    counter = 0
    # flag for testing if coordinates are present in the data
    coordinatesPresent = 'xCord' in data and 'yCord' in data
    if coordinatesPresent:
        displayX = [data['xCord'][0]]
        displayY = [data['yCord'][0]]
        labels = [0]
    # Find the route from the x[i,j] values
    while KeepOn:
        counter = counter + 1
        # Find next on route
        for i in model.nodes:
            if i != curNode and pyomo.value(model.x[curNode, i]) == 1:
                if coordinatesPresent:
                    displayX.append(data['xCord'][i])
                    displayY.append(data['yCord'][i])
                if i > 0:
                    print(i, '->', end='')
                    if coordinatesPresent:
                        labels.append(i)
                else:
                    print(i, end='')
                tmpCurNode = i
        curNode = tmpCurNode
        if curNode < 1:
            break
    # Start plotting the solution to a coordinate system
    if coordinatesPresent:
        plt.plot(displayX, displayY, '-o')
        for i, label in enumerate(labels):
            plt.annotate(label, (displayX[i], displayY[i]))
        plt.show()

def displaySolution(model: pyomo.ConcreteModel(), data: dict):
    print('Solution value is:', pyomo.value(model.obj))
    # Print solution information to prompt
    print('Objective function value =', pyomo.value(model.obj))
    print('Optimal tour is')
    curNode = 0
    print(curNode, '->', end='')
    KeepOn = True
    counter = 0
    # flag for testing if coordinates are present in the data
    coordinatesPresent = 'xCord' in data and 'yCord' in data
    if coordinatesPresent:
        displayX = [data['xCord'][0]]
        displayY = [data['yCord'][0]]
        labels = [0]
    # Find the route from the x[i,j] values
    while KeepOn:
        counter = counter + 1
        # Find next on route
        for i in model.nodes:
            if i != curNode and pyomo.value(model.x[curNode, i]) == 1:
                if coordinatesPresent:
                    displayX.append(data['xCord'][i])
                    displayY.append(data['yCord'][i])
                if i > 0:
                    print(i, '->', end='')
                    if coordinatesPresent:
                        labels.append(i)
                else:
                    print(i, end='')
                tmpCurNode = i
        curNode = tmpCurNode
        if curNode < 1:
            break
    # Start plotting the solution to a coordinate system
    if coordinatesPresent:
        plt.plot(displayX, displayY, '-o')
        for i, label in enumerate(labels):
            plt.annotate(label, (displayX[i], displayY[i]))
        plt.show()

def main(filename: str):
    data = readData(filename)
    model = buildModel(data)
    solveModel(model)
    displaySolution(model, data)


if __name__ == '__main__':
    main('Data_TSP_Arm4')