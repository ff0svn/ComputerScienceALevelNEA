#include <stdlib.h>
#include <Python.h>
#include <stdio.h>

#include "queue.h"

struct cQueue* initQueue(void){
    // An empty queue is represented by a null pointer
    struct cQueue* q = calloc(2, sizeof(struct node));
    q->head = q->tail = NULL;

    return q;
}

int isEmpty(struct cQueue* q){
    return q->head == NULL;
}

void enqueue(struct cQueue* q, PyObject* data){

    Py_INCREF(data);

    if (isEmpty(q)){
        q->head = q->tail = calloc(1, sizeof(struct node));
        
        q->head->data = data;
        q->head->next = NULL;
    } else{
        q->tail->next = calloc(1, sizeof(struct node));

        q->tail = q->tail->next;
        q->tail->data = data;
        q->tail->next = NULL;
    }
}

PyObject* dequeue(struct cQueue* q){
    PyObject* returnValue;
    
    // Store current value of head so can be free-ed
    struct node* temp = q->head;
    returnValue = temp->data;
    
    q->head = q->head->next;
    
    // Don't need to free either of the pointers stored in temp
    // as one is returned and the other is the new head
    free(temp);

    Py_INCREF(returnValue);

    return returnValue;
}

void delQueue(struct cQueue* q){

    while(!(isEmpty(q))){
        struct node* currNode = q->head;
        q->head = currNode->next;

        free(currNode->data);
        free(currNode);
    }

    // As list is now empty can just delete queue
    free(q);
}