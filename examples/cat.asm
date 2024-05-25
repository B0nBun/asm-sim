start:
loop:
       lw $1, $0, input
       beq $1, $0, break
       sw $1, $0, output
       beq $0, $0, loop
break:
       halt