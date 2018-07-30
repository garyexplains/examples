#include <stdio.h>
#include <stdlib.h>
#include <time.h>

typedef struct element {
  int value;
  struct element *next;
  struct element *prev;
  struct element *express;
} element;

element *insert_ordered(element **head, element **tail, int v) {
	element *h = *head;
	if((h == NULL) || (h->value > v)){
		// Empty list or need to insert at start
		element *ne = malloc(sizeof(element));
		ne->value = v;
		ne->next = h;
		ne->prev = NULL;
		ne->express = h;
		if(ne->next!=NULL)
			ne->next->prev = ne;
		if(h == NULL)
			*tail=ne;
		*head=ne;
		return;
	}
	element *p = *head;
	while( (p->next != NULL) && (p->next->value <= v) ) {
		p = p->next;
	}
	// Avoid duplicates, you might want duplicates, so delete
	// this if necessary
	if(p->value==v) return;

	// Now p point to place to insert new element

	// Insert
	element *ne = malloc(sizeof(element));
	ne->value = v;
	ne->next = p->next;
	p->next = ne;
	ne->prev = p;
	if(((rand() %  2) == 0) || (ne->next==NULL)){
		// Randomly (except when last node) update the skip list
		ne->express = p->express;
		p->express = ne;
	}
	if(ne->next==NULL)
		*tail = ne;
	else
		ne->next->prev = ne;
	return;
}

void print_list(element *head) {
	printf("List: ");
	element *p = head;
        while(p != NULL) {
		printf("%d ", p->value);
		p = p->next;
        }
	printf("\n");
}

void print_rev_list(element *tail) {
	printf("Reversed list: ");
	element *p = tail;
        while(p != NULL) {
		printf("%d ", p->value);
		p = p->prev;
        }
	printf("\n");
}

void print_express(element *head) {
	printf("Express: ");
	element *p = head;
        while(p != NULL) {
		printf("%d ", p->value);
		p = p->express;
        }
	printf("\n");
}

int main() {
	int i;

	/* Intializes random number generator */
	srand((unsigned) time(NULL));

	element *head = NULL;
	element *tail = NULL;

	insert_ordered(&head, &tail, 7);
	print_list(head);
	print_rev_list(tail);

	insert_ordered(&head, &tail, 10);
	print_list(head);
	print_rev_list(tail);

	insert_ordered(&head, &tail, 20);
	print_list(head);
	print_rev_list(tail);

	insert_ordered(&head, &tail, 15);
	print_list(head);
	print_rev_list(tail);

	insert_ordered(&head, &tail, 4);
	print_list(head);
	print_rev_list(tail);

	insert_ordered(&head, &tail, 30);
	print_list(head);
	print_rev_list(tail);

	insert_ordered(&head, &tail, 29);
	print_list(head);
	print_rev_list(tail);

	insert_ordered(&head, &tail, 5);
	print_list(head);
	print_rev_list(tail);

	for(i=0;i<100;i++)
		insert_ordered(&head, &tail, rand() % 0xFF);
	print_list(head);
	print_rev_list(tail);
	print_express(head);
}
