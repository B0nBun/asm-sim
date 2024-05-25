start:
addi $1, $0, 1         ; uint16_t x = 1;
addi $2, $0, 1         ; uint16_t y = 1;
addi $3, $0, 0         ; uint16_t z = 0;
addi $4, $0, 0         ; uint16_t sum = 0;
addi $5, $0, 4000000   ; uint16_t until = 4000000;
loop:                  ; do {
    add $3, $1, $2     ;   z = x + y;
    addi $1, $2, 0     ;   x = y;
    addi $2, $3, 0     ;   y = z;
    add $4, $4, $2     ;   sum += z;
    add $3, $1, $2     ;   z = x + y;
    add $3, $3, $2     ;   z += y;
    add $1, $1, $2     ;   x += y;
    addi $2, $3, 0     ;   y = z;
    bleq $2, $5, loop  ; } while (y <= until);
shr $1, $4, 24
sw $1, $0, output
shr $1, $4, 16
sw $1, $0, output
shr $1, $4, 8
sw $1, $0, output
sw $4, $0, output
halt
