module top(input wire clk, input wire i, input wire j, output reg o);
    always @(posedge clk)
        o <= i ^ j;
endmodule
