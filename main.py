import pyomo.environ as pyomo       # Used for modelling the IP
import matplotlib.pyplot as plt     # Used to plot the instance
import math                         # Used to get access to sqrt() function
import readAndWriteJson as rwJson   # Used to read data from Json file

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
    # Define variables
    model.x = pyomo.Var(model.points, model.points, within=pyomo.Binary)
    model.y = pyomo.Var(model.points, within=pyomo.Binary)
    model.rhoMax = pyomo.Var(within=pyomo.NonNegativeReals)
    # Add objective function
    model.obj = pyomo.Objective(expr=model.rhoMax)
    # Add "all represented" constraints
    model.allRep = pyomo.ConstraintList()
    for j in model.points:
        model.allRep.add(expr=sum(model.x[i, j] for i in model.points) == 1)
    # Add only represent if y[i]=1
    model.GUB = pyomo.ConstraintList()
    for i in model.points:
        for j in model.points:
            model.GUB.add(expr=model.x[i, j] <= model.y[i])
    # Add cardinality constraint on number of groups
    model.cardinality = pyomo.Constraint(expr=sum(model.y[i] for i in model.points) == model.k)
    # Add correct definition of the rhoMax variable
    model.rhoMaxDef = pyomo.ConstraintList()
    for j in model.points:
        model.rhoMaxDef.add(expr=sum(model.dist[i][j]*model.x[i, j] for i in model.points) <= model.rhoMax)
    # Fix x[i][i] == y[i]
    model.fixXandY = pyomo.ConstraintList()
    for i in model.points:
        model.fixXandY.add(expr=model.x[i,i]==model.y[i])
    return model


def solveModel(model: pyomo.ConcreteModel()):
    # Set the solver
    solver = pyomo.SolverFactory('gurobi')
    # Solve the model
    solver.solve(model, tee=True)


def displaySolution(model: pyomo.ConcreteModel()):
    labels = [0]*model.nrPoints
    # Print the groups to promt and save coordinates for plotting
    for i in model.points:
        if pyomo.value(model.y[i]) == 1:
            print('Point', i, 'represents points:')
            for j in model.points:
                if pyomo.value(model.x[i, j]) == 1:
                    print (j,",",end='')
                    labels[j] = i
            print('\n')
    # Plot with different colors
    plt.scatter(model.xCoordinates, model.yCoordinates, c=labels)
    plt.show()



def main(clusterDataFile: str):
    data = readData(clusterDataFile)
    model = buildModel(data)
    solveModel(model)
    displaySolution(model)


if __name__ == '__main__':
    theDataFile = "Data_Med_Depot"
    main(theDataFile)