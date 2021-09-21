import os, sys, time

#########################################################################################
#########################################################################################

#if len(sys.argv) != 3:
#	print '''Usage: {0}
#	<input>
#	<output>\n\n\n'''.format(sys.argv[0])
#	sys.exit()

finput, foutput = sys.argv[1:]

# Section 1: Reading into memory
# ignore the ModelPeriodCostByRegion with years
OUT = open(foutput,'w')
with open(finput) as IN:
	lines = []
	t1 = time.time()
	for line in IN:
		if "<variable name=" in line:
			if "ModelPeriodCostByRegion" not in line :
				lst = line.strip().split()	
				lines.append(lst)
			else :
				print line
t2 = time.time() - t1
print "It takes ", t2, "seconds to read the file"
# 142869892 lines
print "The number of lines: ", len(lines)

# Sort the Lists
sortedList = sorted(lines)
print "The number of sorted lines: ", len(sortedList)

t3 = time.time() - t1
print "It takes ", t3 , "seconds to sort the lists"

# Save the sorted list
#output2 = open("Kenya_BIG_ALL_sorted.sol","w")
#for l in sortedList :
#        output2.write("%s\n" % l)
#t2 = time.time() - t1
#print "It takes ", t2, "seconds to save the file"


# Each variable include 29 numbers between 2016-2040
nblocks = 2040-2016+1
old = ''
ii = 1
values = []

for each in sortedList:
	# Assign the values after '=' in variable name= to the variable variableContents
	# This involves replacing '"', and ')', and adding a ',' instead of '(', and then splitting at ','        
        variableContents = each[1].replace('(',',').replace(")",'').replace('name=','').replace('"','').split(',')

	# The contents of variableContents are then joined and saved as the variable 'variable'. This involves starting of with the 0th element and joining elements 1 to -1 (2nd last) between parentheses.
        variable = variableContents[0]+'\t'+'\t'.join(variableContents[1:-1])

	# Get the values
        value = each[-2].replace('"','').split('=')[1]
        values.append(value)
        if (ii % nblocks == 0 ) :
                totalvalue = sum(float(i) for i in (values))
                # only consider non-zero values
                if (totalvalue > 1e-15) :                
                        #print variable, values, totalvalue
                        OUT.write("\n{0} ".format(variable))
                        OUT.write("\t".join(values))

                values = []

	if (ii % 1000000 == 0) :
              	print "Read at line:", ii
        ii += 1

t2 = time.time()
print 'This process took ', t2-t1 , 's'
