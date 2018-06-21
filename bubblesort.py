#
# Understanding Bubble Sort with Examples and Code!
# https://youtu.be/WOjc48sVo6E
#
def bubblesort(list):
        swapped = True
        while swapped:
                print
                print "New iteration..."
                swapped = False
                for i in range(len(list)-1):
                        if(list[i] > list[i+1]):
                                print "Index: " + str(i) + " - Swap " + str(list[i]) + " with " + str(list[i+1])
                                tmp = list [i]
                                list[i] = list[i+1]
                                list[i+1] = tmp
                                swapped = True
                                print list
        print "Nothing left to swap. Done"
        return list

l = [5,8,1,4,2]
print l

l = bubblesort(l)
print l
