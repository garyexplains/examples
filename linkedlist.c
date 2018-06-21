#include <stdio.h>
#include <stdlib.h>

typedef struct element {
  int value;
  struct element *next;
} element;

element *insert_ordered(element *head, int v) {
        if((head == NULL) || (head->value > v)){
                // Empty list or need to insert at start
                element *ne = malloc(sizeof(element));
                ne->value = v;
                ne->next = head;
                return ne;
        }
        element *p = head;
        while( (p->next != NULL) && (p->next->value < v) ) {
                p = p->next;
        }
        // Now p point to place to insert new element
        element *ne = malloc(sizeof(element));
        ne->value = v;
        ne->next = p->next;
        p->next = ne;
        return head;
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

int main() {
        element *head = NULL;
        head = insert_ordered(head, 7);
        print_list(head);
        head = insert_ordered(head, 10);
        print_list(head);
        head = insert_ordered(head, 20);
        print_list(head);
        head = insert_ordered(head, 15);
        print_list(head);
        head = insert_ordered(head, 4);
        print_list(head);
        head = insert_ordered(head, 30);
        print_list(head);
        head = insert_ordered(head, 29);
        print_list(head);
        head = insert_ordered(head, 5);
        print_list(head);
}
