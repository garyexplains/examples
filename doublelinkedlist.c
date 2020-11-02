// Copyright 2019-2020 Gary Sims
//
// To get a copy use git or:
// curl https://raw.githubusercontent.com/garyexplains/examples/master/doublelinkedlist.c --output doublelinkedlist.c
//
// To compile use:
// gcc -O3 -o doublelinkedlist doublelinkedlist.c
//

#include <stdio.h>
#include <stdlib.h>

typedef struct element {
  int value;
  struct element *next;
  struct element *prev;
} element;

element *insert_ordered(element **head, element **tail, int v) {
	element *h = *head;
	if((h == NULL) || (h->value > v)){
		// Empty list or need to insert at start
		element *ne = malloc(sizeof(element));
		ne->value = v;
		ne->next = h;
		ne->prev = NULL;
		if(ne->next!=NULL)
			ne->next->prev = ne;
		if(h == NULL)
			*tail=ne;
		*head=ne;
		return NULL;
	}
	element *p = *head;
	while( (p->next != NULL) && (p->next->value < v) ) {
		p = p->next;
	}
	// Now p point to place to insert new element
	element *ne = malloc(sizeof(element));
	ne->value = v;
	ne->next = p->next;
	p->next = ne;
	ne->prev = p;
	if(ne->next==NULL)
		*tail = ne;
	else
		ne->next->prev = ne;
	return NULL;
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

int main() {
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
}
