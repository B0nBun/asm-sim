question: "What is your name?\n\0"
hello: "Hello, "
name_buffer: "\0\0\0\0\0\0\0\0\0\0"

start:
    addi $1, $0, 0
question_loop:
    lw $2, $1, question
    beq $2, $0, scan_start
    sw $2, $0, output
    addi $1, $1, 1
    beq $0, $0, question_loop

scan_start:
    addi $1, $0, 0
scan_loop:
    lw $2, $0, input
    beq $2, $0, hello_start
    sw $2, $1, name_buffer
    addi $1, $1, 1
    beq $0, $0, scan_loop

hello_start:
    addi $1, $0, 0
hello_loop:
    lw $2, $1, hello
    beq $2, $0, hello_break
    sw $2, $0, output
    addi $1, $1, 1
    beq $0, $0, hello_loop
hello_break:
    halt
