class sort:
    # Performs merge sort on the given array

    @staticmethod
    def sort(array: list, key = lambda x: x):
        if len(array) == 1:
            return array

        arrayA = array[:len(array) // 2]
        arrayB = array[len(array) // 2:]

        return sort.merge(sort.sort(arrayA, key), sort.sort(arrayB, key), key)
    
    @staticmethod
    def merge(arrayA: list, arrayB: list, key):
        returnList = []

        aPtr = 0
        bPtr = 0

        # Iterate through all the elements
        # of array A and array B, adding them
        # to returnList in a sorted order   
        while aPtr < len(arrayA) and bPtr < len(arrayB):
            if key(arrayA[aPtr]) > key(arrayB[bPtr]):
                returnList.append(arrayB[bPtr])

                bPtr += 1
            else:
                returnList.append(arrayA[aPtr])

                aPtr += 1

        # As we know array A and B are both sorted
        # if all the elements of one are less than
        # the other, we can append the remaining
        # items to the end of returnList

        if aPtr >= len(arrayA):
            for item in arrayB:
                returnList.append(item)
        else:
            for item in arrayA:
                returnList.append(item)
        
        return returnList