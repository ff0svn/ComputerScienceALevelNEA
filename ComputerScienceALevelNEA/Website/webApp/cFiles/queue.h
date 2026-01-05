#ifndef QUEUE
#define QUEUE

#include <ctype.h>


struct cQueue{
    struct node* head;
    struct node* tail;
};

struct node{
    PyObject* data;
    struct node* next;
};

struct cQueue* initQueue(void);
void delQueue(struct cQueue* q);
void enqueue(struct cQueue* q, PyObject* data);
PyObject* dequeue(struct cQueue* q);
int isEmpty(struct cQueue* q);

#endif