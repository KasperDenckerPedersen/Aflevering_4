import pyomo.environ as pyomo  # Used for modelling the IP
import matplotlib.pyplot as plt  # Used to plot the instance
import math  # Used to get access to sqrt() function
import readAndWriteJson as rwJson  # Used to read data from Json file

def readData(clusterData: str) -> dict():
    data = rwJson.readJsonFileToDictionary(clusterData)
    data['nrPoints'] = len(data['x'])
    return data


def buildModel(data: dict) -> pyomo.ConcreteModel():
    # Create model
    model = pyomo.ConcreteModel()
    # Copy data to model object
    model.nrPoints = data['nrPoints']
    model.points = range(0, data['nrPoints'])
    model.xCoordinates = data['x']
    model.yCoordinates = data['y']
    model.dist = data['Distance']
    model.k = data['k']
    model.groups = range(0, model.k)
    # Define variables
    model.x = pyomo.Var(model.points, model.groups, within=pyomo.Binary)
    model.D = pyomo.Var(model.groups, within=pyomo.NonNegativeReals)
    model.Dmax = pyomo.Var(within=pyomo.NonNegativeReals)
    # Add objective function
    model.obj = pyomo.Objective(expr=model.Dmax)
    # Add definition for Dmax
    model.DmaxDef = pyomo.ConstraintList()
    for l in model.groups:
        model.DmaxDef.add(expr=model.D[l] <= model.Dmax)
    # Add defintion for the D-variables
    model.Ddef = pyomo.ConstraintList()
    for i in model.points:
        for j in model.points:
            if i != j:
                for l in model.groups:
                    model.Ddef.add(expr=model.D[l] >= model.dist[i][j] * (model.x[i, l] + model.x[j, l] - 1))
    # Make sure that all points a in a group
    model.assignAll = pyomo.ConstraintList()
    for i in model.points:
        model.assignAll.add(expr=sum(model.x[i, l] for l in model.groups) == 1)
    #Fix hver arm i hver sit cluster
    model.fixArm1 = pyomo.Constraint()
    model.x[0, 0].fix(1)

    model.fixArm2 = pyomo.Constraint()
    model.x[1,1].fix(1)

    model.fixArm3 = pyomo.Constraint()
    model.x[97, 2].fix(1)

    model.fixArm4 = pyomo.Constraint()
    model.x[167,3].fix(1)
    return model


def solveModel(model: pyomo.ConcreteModel()):
    # Set the solver
    solver = pyomo.SolverFactory('gurobi')
    # Solve the model
    solver.solve(model, tee=True)


def displaySolution(model: pyomo.ConcreteModel()):
    print('Optimal diameter is:',pyomo.value(model.obj))
    labels = [0] * model.nrPoints
    ptNumber = list(model.points)
    # Print the groups to promt and save coordinates for plotting
    for l in model.groups:
        print('Group',l,'consists of:')
        for i in model.points:
            if pyomo.value(model.x[i,l]) == 1:
                print(model.yCoordinates[i], ',', end='')
                labels[i] = l
        print('')
    # Plot with different colors
    plt.scatter(model.xCoordinates, model.yCoordinates, c=labels)
    for i, label in enumerate(ptNumber):
        plt.annotate(ptNumber[i], (model.xCoordinates[i], model.yCoordinates[i]))
    plt.show()
    # Print the groups to promt and save coordinates for plotting
    for i in model.points:
        if pyomo.value(model.y[i]) == 1:
            print('Point', i, 'represents points:')
            for j in model.points:
                if pyomo.value(model.x[i, j]) == 1:
                    print(j, ",", end='')
                    labels[j] = i
            print('\n')

def main(clusterDataFile: str):
    data = readData(clusterDataFile)
    model = buildModel(data)
    solveModel(model)
    displaySolution(model)


if __name__ == '__main__':
    theDataFile = "Data_Med_Depot"
    main(theDataFile)