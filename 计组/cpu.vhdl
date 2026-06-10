library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;
use IEEE.NUMERIC_STD.ALL; -- Uncomment the following library declaration if using
-- arithmetic functions with Signed or Unsigned values
--use IEEE.NUMERIC_STD.ALL; -- Uncomment the following library declaration if instantiating
-- any Xilinx primitives in this code. --library UNISIM; --use UNISIM.VComponents.all;
entity CPU is
Port(
clk : in STD_LOGIC; --时钟
run_k : in STD_LOGIC;--运行
rst : in STD_LOGIC; --复位
input : in STD_LOGIC_VECTOR (15 downto 0);--拨码开关
light : out STD_LOGIC_VECTOR (15 downto 0); --LED 灯
ADDR : out STD_LOGIC_VECTOR (15 downto 0); --地址线
DATA : inout STD_LOGIC_VECTOR (15 downto 0); --数据线
RAM1_EN : out STD_LOGIC; --片选（低有效）
RAM1_WE : out STD_LOGIC; --写使能（低有效）
RAM1_OE : out STD_LOGIC; --读使能（低有效）
stateCnt1: out STD_LOGIC_VECTOR (6 downto 0);--对应左侧七段数码管);
stateCnt2: out STD_LOGIC_VECTOR (6 downto 0);--对应右侧七段数码管);
DBC : out STD_LOGIC
);
end CPU ;
architecture Behavioral of CPU is
--寄存器
type dimVector is array (7 downto 0) of std_logic_vector (15 downto 0); -- 总状态
type StatePro is(
build, --写程序
run --执行程序
);
-- 程序执行状态
type StateEnum is (
getIns, -- 取指阶段：从指令存储器获取指令
decode, -- 译码阶段：解析指令并准备操作数
execute, -- 执行阶段：执行算术/逻辑运算
queryMemory,-- 访存阶段：访问数据存储器
writeBack -- 写回阶段：将结果写回寄存器
);-- 写主存状态
type StateSram is(
waiting, prepare, start, achieve, over
);-- 访存状态
type StateQuery is(
pre, query, hold, finish
);
signal PC : std_logic_vector (15 downto 0) := x"0000"; --程序计数器
signal IR : std_logic_vector (15 downto 0) := x"0000";--指令寄存器
--通用寄存器
signal Reg : dimVector := (
x"0000", x"0000", x"0000", x"0000", x"0000", x"0000", x"0000", x"0000"
);
signal temp_statePro : StatePro := build; --初始化总状态
signal temp_stateEnum : StateEnum := getIns; --初始化程序执行状态
signal temp_stateSram : StateSram := prepare; --初始化写主存状态
signal temp_stateQuery : StateQuery := pre; --初始化访存状态
signal to_light : std_logic_vector (15 downto 0); --LED 灯的信号
signal temp_data : std_logic_vector (15 downto 0); --数据
signal temp_addr : std_logic_vector (15 downto 0); --地址
--操作过程中的量
signal opt : std_logic_vector (4 downto 0); --操作码
signal rx : std_logic_vector (2 downto 0); --rx 寄存器
signal ry : std_logic_vector (2 downto 0); --ry 寄存器
signal rz : std_logic_vector (2 downto 0); --rz 寄存器
signal imme : std_logic_vector (15 downto 0); --立即数
signal func : std_logic_vector (1 downto 0); --功能码
signal ACC : std_logic_vector (15 downto 0); --运算器结果
signal MBR : std_logic_vector (15 downto 0); --数据缓冲寄存器
begin
--灯的控制
light<=to_light; --总状态的切换
process(rst,run_k)
begin
if rst='0' then
temp_statePro<=build; --重置时先开始写程序
StateCnt1 <= not "1000000";
elsif rising_edge(run_k) then
case temp_statePro is
when build => --写完开始执行
StateCnt1 <= not "1111001";
temp_statePro<=run;
when run => --执行完再写
StateCnt1 <= not "1000000";
temp_statePro<=build;
end case;
end if;
end process; --主状态机
process(rst,clk,temp_statePro)
begin
if rst='0' then
temp_data<=x"0000";
temp_addr<=x"0000";
to_light<=x"0000";
PC<=x"0000";
IR<=x"0000";
RAM1_EN<='1';
RAM1_OE<='0';
RAM1_WE<='0';
temp_stateEnum<=getIns;
temp_stateSram<=waiting;
temp_stateQuery<=query;
StateCnt2 <= not "0000000";
elsif rising_edge(clk) then
case temp_statePro is
--写程序的过程
when build =>
case temp_stateSram is
when waiting =>
temp_addr <= input;
StateCnt2 <= not"1000000";
temp_stateSram <= prepare;
when prepare =>
temp_data <= input;
RAM1_EN <= '0';
RAM1_OE <= '1';
RAM1_WE <= '1';
ADDR <= temp_addr;
DATA <= temp_data;
StateCnt2 <= not"1111001";
temp_stateSram <= start;
when start =>
ADDR <= temp_addr;
DATA <= temp_data;
RAM1_WE <= '0';
RAM1_OE <= '1';
StateCnt2 <= not"0100100";
temp_stateSram <= achieve;
when achieve =>
RAM1_WE <= '0';
RAM1_OE <= '1';
to_light <= DATA;
StateCnt2 <= not"0110000";
temp_stateSram <= over;
when over =>
RAM1_EN <= '1';
RAM1_OE <= '0';
RAM1_WE <= '0';
StateCnt2 <= not"0011001";
temp_stateSram <= waiting;
end case; --执行程序的过程
when run =>
case temp_stateEnum is
--取指周期
when getIns => --0
StateCnt2 <= not"1000000";
case temp_stateQuery is
when pre =>
RAM1_EN <= '0';
RAM1_OE <= '1';
RAM1_WE <= '1';
ADDR <= PC;
DATA <= (others=>'Z');
temp_stateQuery <= query;
when query =>
RAM1_OE <= '0';
RAM1_WE <= '1';
ADDR <= PC;
temp_stateQuery <= hold;
when hold =>
RAM1_OE <= '0';
RAM1_WE <= '1';
IR <= DATA;
temp_stateQuery <= finish;
when finish =>
RAM1_EN <= '1';
RAM1_OE <= '0';
RAM1_WE <= '0';
temp_stateQuery <= pre;
temp_stateEnum <= decode;
PC <= PC+1;
end case; --译码周期
when decode => --1
StateCnt2 <= not"1111001";
opt <= IR(15 downto 11); --取操作码
case opt is
--ADDIU
when "01001" =>
rx <= IR(10 downto 8); --取 rx 寄存器
--取立即数并扩展
if IR(7)='0' then
imme <= "00000000"&IR(7 downto 0);-- 正 数
的扩展
else
imme <= "11111111"&IR(7 downto 0); -- 负 数
的扩展
end if;
temp_stateEnum<=execute; --ADDU/SUBU
when "11100" => --ADDU/SUBU/SLL
rx <= IR(10 downto 8); --取 rx 寄存器
ry <= IR(7 downto 5); --取 ry 寄存器
rz <= IR(4 downto 2); --取 rz 寄存器
func <= IR(1 downto 0);--取功能码
temp_stateEnum<=execute;
when "01101" =>
rx <= IR(10 downto 8); --取 rx 寄存器
imme <= "00000000"&IR(7 downto 0);-- 取 立 即 数
并扩展
temp_stateEnum<=execute; --LW
when "10011" =>
rx <= IR(10 downto 8); --取 rx 寄存器
ry <= IR(7 downto 5); --取 ry 寄存器
--取立即数并扩展
if IR(4)='0' then
imme <= "00000000000"&IR(4 downto 0); -- 正数扩展
else
imme <= "11111111111"&IR(4 downto 0); -- 负数扩展
end if;
temp_stateEnum<=execute; --SW
when "11011" =>
rx <= IR(10 downto 8); --取 rx 寄存器
ry <= IR(7 downto 5); --取 ry 寄存器
--取立即数并扩展
if IR(4)='0' then
imme <= "00000000000"&IR(4 downto 0); -- 正数扩展
else
imme <= "11111111111"&IR(4 downto 0); -- 负数扩展
end if;
temp_stateEnum<=execute; --BNEZ
when "00101" =>
rx <= IR(10 downto 8); --取 rx 寄存器
--取立即数并扩展
if IR(7)='0' then
imme <= "00000000"&IR(7 downto 0);-- 正 数
扩展
else
imme <= "11111111"&IR(7 downto 0); -- 负 数
扩展
end if;
temp_stateEnum<=execute; --BNEZ
when "00001" => --BEQZ
rx <= IR(10 downto 8);
if IR(7)='0' then
imme <= "00000000"&IR(7 downto 0);
else
imme <= "11111111"&IR(7 downto 0);
end if;
temp_stateEnum<=execute;
when "00010" => --JALR
rx <= IR(10 downto 8);
ry <= IR(7 downto 5);
temp_stateEnum<=execute;
when others =>
temp_stateEnum<=getIns;
end case; --执行周期
-- ================= 执行阶段 =================
when execute =>
StateCnt2 <= not "0100100"; -- 状态'2'
case opt is
when "01001" => -- ADDIU
ACC <= imme +
Reg(to_integer(unsigned(rx)));
temp_stateEnum <= writeBack;
when "11100" => -- ADDU/SUBU/SLL
if func = "01" then
ACC <= Reg(to_integer(unsigned(rx))) +
Reg(to_integer(unsigned(ry)));
elsif func = "10" then
ACC <= Reg(to_integer(unsigned(rx))) - Reg(to_integer(unsigned(ry)));
elsif func = "11" then --SLL: Rz = Rx << Ry
ACC <= std_logic_vector(shift_left(unsigned(Reg(to_integer(unsigned(rx)))), to_integer(unsigned(Reg(to_integer(unsigned(ry)))))));
end if;
temp_stateEnum <= writeBack;
when "01101" => -- LI
ACC <= imme;
temp_stateEnum <= writeBack;
when "10011" => -- LW
ACC <= imme +
Reg(to_integer(unsigned(rx)));
temp_stateEnum <=
queryMemory;
when "11011" => -- SW
ACC <= imme +
Reg(to_integer(unsigned(rx)));
temp_stateEnum <=
queryMemory;
when "00101" => -- BNEZ
if IR(7) = '0' then
imme <= "00000000" & IR(7 downto 0);
elsif IR(7) = '1' then
imme <= "11111111" & IR(7 downto 0);
end if;
temp_stateEnum <= writeBack;
when "00001" => -- BEQZ
temp_stateEnum <= writeBack;
when "00010" => -- JALR
ACC <= PC;
temp_stateEnum <= writeBack;
when others => -- 无效操作码
temp_stateEnum <= getIns;
end case; --访存周期
when queryMemory =>
StateCnt2 <= not"0110000";
case opt is
--LW
when "10011" =>
case temp_stateQuery is
when pre =>
RAM1_EN <= '0';
RAM1_OE <= '1';
RAM1_WE <= '1';
ADDR <= ACC;
DATA <= (others=>'Z');
temp_stateQuery <= query;
when query =>
RAM1_OE <= '0';
RAM1_WE <= '1';
ADDR <= ACC;
temp_stateQuery <= hold;
when hold =>
RAM1_OE <= '0';
RAM1_WE <= '1';
MBR <= DATA;
temp_stateQuery <= finish;
when finish =>
RAM1_EN <= '1';
RAM1_OE <= '0';
RAM1_WE <= '0';
temp_stateQuery <= pre;
temp_stateEnum <= writeBack;
end case; --SW
when "11011" =>
case temp_stateQuery is
when pre =>
RAM1_EN <= '0';
RAM1_OE <= '1';
RAM1_WE <= '1';
ADDR <= ACC;
DATA <= Reg(to_integer(unsigned(ry)));
temp_stateQuery <= query;
when query =>
ADDR <= ACC;
DATA <= Reg(to_integer(unsigned(ry)));
RAM1_WE <= '0';
RAM1_OE <= '1';
temp_stateQuery <= hold;
when hold =>
RAM1_WE <= '0';
RAM1_OE <= '1';
temp_stateQuery <= finish;
when finish =>
RAM1_EN <= '1';
RAM1_OE <= '0';
RAM1_WE <= '1';
temp_stateQuery <= pre;
temp_stateEnum <= writeBack;
end case; --遇到错误码，重新取指
when others =>
temp_stateEnum <= getIns;
end case; --写回周期
when writeBack =>
StateCnt2 <= not"0011001";
case opt is
--ADDIU
when "01001" =>
Reg(to_integer(unsigned(rx)))<=ACC; --ADDU/SUBU
when "11100" =>
Reg(to_integer(unsigned(rz)))<=ACC; --LI
when "01101" =>
Reg(to_integer(unsigned(rx)))<=ACC; --LW
when "10011" =>
Reg(to_integer(unsigned(ry)))<=MBR; --SW
when "11011" =>
null; --BNEZ
when "00101" => --BNEZ
if Reg(to_integer(unsigned(rx))) = "0000000000000000"
then
PC <= PC;
else
PC <= PC + imme;
end if;
when "00001" => --BEQZ
if Reg(to_integer(unsigned(rx))) = "0000000000000000"
then
PC <= PC + imme;
else
PC <= PC;
end if;
when "00010" => --JALR
Reg(to_integer(unsigned(ry))) <= ACC;
PC <= Reg(to_integer(unsigned(rx)));
when others =>
null;
end case;
temp_stateEnum <= getIns;
end case;
end case;
end if;
end process;
DBC <= '1';
end Behavioral;