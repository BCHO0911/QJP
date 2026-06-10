--��׼΢�ţ�NCEPUljxx
--���˾�Ϊ����������

--�����ܶ�/�����ϵ����
--�쿨/ˢ����/��װ��������
--�޸����ĸ�ʽ/���ؿμ�
--���v��NCEPUljxx
----------------------------------------------------------------------------------
-- Company: 
-- Engineer: 
-- 
-- Create Date:    21:09:39 05/28/2025
-- Design Name: 
-- Module Name:    cpu - Behavioral 
-- Project Name: 
-- Target Devices: 
-- Tool versions: 
-- Description:     
-- Dependencies: 
--
-- Revision: 
-- Revision 0.01 - File Created
-- Additional Comments: 
--
----------------------------------------------------------------------------------
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;     
use IEEE.STD_LOGIC_UNSIGNED.ALL; 
use IEEE.STD_LOGIC_ARITH.ALL;    

entity cpu is
    Port ( 
        clk      : in  STD_LOGIC;                             
        rst      : in  STD_LOGIC;                             
        input    : in  STD_LOGIC_VECTOR (15 downto 0);        
        output   : out STD_LOGIC_VECTOR (15 downto 0);        
        seg      : out STD_LOGIC_VECTOR (13 downto 0);        
        ram_en   : out STD_LOGIC;                             -- RAMʹ���źţ�ͨ���͵�ƽ��Ч ('0')
        ram_oe   : out STD_LOGIC;                             -- RAM���ʹ���ź� (��)���͵�ƽ��ЧʱRAM�������
        ram_rw   : out STD_LOGIC;                             -- RAM��/д�����ź� (д)��'0'��ʾд��'1'��ʾ��
        ram_addr : out STD_LOGIC_VECTOR (17 downto 0);        -- 18λRAM��ַ�����CPUָ�����ʵ�RAM��Ԫ
        DBC      : out STD_LOGIC;                             -- ����������źţ����ڵ��Կ��ƻ�״ָ̬ʾ
        ram_data : inout STD_LOGIC_VECTOR (15 downto 0)      -- 16λ˫��RAM�������ߣ�CPU��RAM֮�䴫������
    );
end cpu;


architecture Behavioral of cpu is

    signal state : STD_LOGIC_VECTOR (3 downto 0) := "0000"; 

    -- ͨ�üĴ�������
    signal r0 : STD_LOGIC_VECTOR (15 downto 0) := "0000000000000000"; -- �Ĵ���R0����ʼֵΪ0
    signal r1 : STD_LOGIC_VECTOR (15 downto 0) := "0000000000000000"; -- �Ĵ���R1����ʼֵΪ0
    signal r2 : STD_LOGIC_VECTOR (15 downto 0) := "0000000000000001"; -- �Ĵ���R2����ʼֵΪ1
    signal r3 : STD_LOGIC_VECTOR (15 downto 0) := "0000000000000001"; -- �Ĵ���R3����ʼֵΪ1
    signal r4 : STD_LOGIC_VECTOR (15 downto 0) := "0000000000000100"; -- �Ĵ���R4����ʼֵΪ4
    signal r5 : STD_LOGIC_VECTOR (15 downto 0) := "0000000000000101"; -- �Ĵ���R5����ʼֵΪ5
    signal r6 : STD_LOGIC_VECTOR (15 downto 0) := "0000000000000110"; -- �Ĵ���R6����ʼֵΪ6
    signal r7 : STD_LOGIC_VECTOR (15 downto 0) := "0000000000000111"; -- �Ĵ���R7����ʼֵΪ7

    signal ir : STD_LOGIC_VECTOR (15 downto 0) := "0000000000000000"; 
    signal pc : STD_LOGIC_VECTOR (15 downto 0) := "0000000000010000";

    -- ���̺������壺rr  - ���ڴ�ͨ�üĴ����ж�ȡֵ
    -- ���� a: 3λ�Ĵ������ (000-111 ��Ӧ R0-R7)
    -- ��� b: 16λ�Ĵ����е�����
    procedure rr(a : in STD_LOGIC_VECTOR (2 downto 0); b : out STD_LOGIC_VECTOR (15 downto 0)) is 
    begin
        case a is
            when "000" => b := r0;
            when "001" => b := r1;
            when "010" => b := r2;
            when "011" => b := r3;
            when "100" => b := r4;
            when "101" => b := r5;
            when "110" => b := r6;
            when "111" => b := r7;
            when others => b := "0000000000000000";
        end case;
    end rr;

begin 

    process (clk, rst)
        
        variable mar  : STD_LOGIC_VECTOR (15 downto 0) := "0000000000010000"; 
        variable mbr  : STD_LOGIC_VECTOR (15 downto 0) := "0000000000000000"; 
        variable op   : STD_LOGIC_VECTOR (4 downto 0)  := "00000";           
        variable rx, ry, RZ : STD_LOGIC_VECTOR (2 downto 0) := "000";        
        variable imme : STD_LOGIC_VECTOR (15 downto 0) := "0000000000000000"; 
        variable t1, t2, t3 : STD_LOGIC_VECTOR (15 downto 0) := "0000000000000000"; 
    begin
   
        if (rst = '0') then
            state  <= "0000";                         
            output <= "0000000000000000";             
            mar    := "0000000000010000";             -- MAR��λ��PC�ĳ�ʼֵ
            pc     <= "0000000000010000";             -- PC��λ����ʼ��ַ 0x0010
        
        elsif (CLK'event and CLK = '0') then
            case state is 

                -- ״̬ "0000": ��ʼ״̬ / ģʽѡ��
                -- �����ⲿ input(2 downto 0) ��ֵ������һ��״̬
                -- "001": ����RAMд��ģʽ
                -- "011": ����������ȡִָ��ģʽ
                when "0000" => -- ��ʼ״̬ 00
                    DBC <= '1'; 
                    case input(2 downto 0) is
                        when "001" => 
                            state <= "0001"; -- ת����״̬ "0001" (׼����RAMд���ַ)
                            DBC <= '1';
                        when "011" => 
                            state <= "0011"; -- ת����״̬ "0011" (��ʼȡָ)
                            DBC <= '1';
                            ram_data <= "ZZZZZZZZZZZZZZZZ"; -- CPU�����������ø��裬׼��RAM����
								when "111" =>
									 state <= "1001"; -- ת����״̬ "1001" (������/RAM������)
									 DBC <= '1';
                        when others =>
                            null; -- ��������ֵ�����ֵ�ǰ״̬���޲���
                    end case;
						  
                    output <= input; 

                -- ״̬ "0001": ������д�����ݺ�ָ�� - ��ַ���ý׶�
                -- ʹ�� input �ĵ�16λ��ΪRAM��ַ (����λ�̶�Ϊ"00")
                when "0001" => -- ������д�����ݺ�ָ�� 01
                    output   <= input;
                    DBC      <= '1';
                    ram_addr <= "00" & input;       -- ����RAM��ַ������λΪ"00"����16λ����input
                    ram_en   <= '0';                -- ʹ��RAM
                    ram_oe   <= '1';                -- RAM�����ֹ (��ΪCPUҪ׼��д����д���ַ)
                    ram_rw   <= '1';                -- RAM����Ϊ��ģʽ (��������ǵ�ַ�ȶ��׶Σ�ʵ��д����һ����)
                    state    <= "0010";             -- ת����״̬ "0010" (׼��д������)

                -- ״̬ "0010": ������д�����ݺ�ָ�� - ����д��׶�
                -- �� input ������д�뵽��һ���������õ�RAM��ַ
                when "0010" => -- 02
                    DBC      <= '1';
                    ram_data <= input;              -- ��input�����ݷŵ�ram_data�����ϣ���CPU����
                    output   <= input;
                    ram_en   <= '0';                -- RAM����ʹ��
                    ram_oe   <= '1';                -- RAM�����ֹ
                    ram_rw   <= '0';                -- RAM����Ϊдģʽ����ram_data�ϵ�����д��RAM
                    state    <= "0001";             -- ����״̬ "0001"�����Լ���д����һ����ַ������


                -- ״̬ "1001": ������/RAM�����ݣ������ַ״̬
					 when "1001" => -- ��״̬
                    output   <= input;
						  ram_addr <= "00" & input;
                    DBC      <= '1';
						  ram_en   <= '0'; 
						  ram_oe   <= '1'; 
						  ram_rw   <= '0'; 
						  case input(1 downto 0) is
								when "00" => -- ����
									state   <= "1010"; 
								when "11" => -- RAM
									rx  := input(4 downto 2);
								   state   <= "1100"; 
									rr(rx, t1);
								when others =>
                           null; -- ��������ֵ�����ֵ�ǰ״̬���޲���
						  end case;   
						  
                -- ״̬ "1010": ����������ݣ���������״̬
					 when "1010" => -- ���������ַ
					     ram_addr <= "00" & input;
						  output   <= input;
                    DBC      <= '1';
						  ram_en   <= '0'; 
						  ram_oe   <= '1'; 
						  ram_rw   <= '0';  
						  state    <= "1011";       				 	  
						  
					 when "1011" => -- �����������				 
                    output   <= ram_data;
                    DBC      <= '1';
						  ram_en   <= '0'; 
						  ram_oe   <= '1'; 
						  ram_rw   <= '1'; 
						  state    <= "1001";      
						  
					 when "1100" => -- ���RAM����
                    DBC      <= '1';
						  ram_en   <= '0'; 
						  ram_oe   <= '1'; 
						  ram_rw   <= '1'; 
                    output   <= t1;
						  state    <= "1001";    
						  
                -- ״̬ "0011": ȡָ�׶�
                -- MAR�д�ŵ���PC��ֵ (����ǰҪȡ��ָ���ַ)
                when "0011" => -- ȡָ�׶� 11
                   
                    DBC      <= '1';
                    state    <= "1111";             -- ��һ��״̬�� "1111" (�ȴ�RAM���ݷ���)
                    ram_addr <= "00" & pc;         -- ��MAR(ֵΪPC)��ΪRAM��ַ (����λ��0)
                    ram_data <= "ZZZZZZZZZZZZZZZZ"; -- CPU�����������ø��裬׼����RAM����ָ��
                    output   <= mar;                -- �����ǰָ���ַ��output�˿� (���ڵ���)
						  ram_en   <= '0';                -- ʹ��RAM
                    ram_oe   <= '0';                -- RAM���ʹ�� (RAM�����������ߣ���������)
                    ram_rw   <= '1';                -- RAM����Ϊ��ģʽ

                -- ״̬ "1111": ȡָ�׶� (IF) - Phase 2: ��RAM��ȡָ��, PC����
                -- �����ʱRAM�ѽ�ָ�����ݷŵ���ram_data������
                WHEN "1111" =>   -- 12 (ע����״̬�벻һ�£���Ϊȡָ���) �ı�ʹ���ź� PC+1
                    DBC      <= '1';
                    ram_en   <= '0';                -- RAM����ʹ�� (ͨ��CPU�������ݺ�RAM��ֹͣ����)
                    ram_oe   <= '1';                -- RAM�����ֹ (CPU��ȡ�����ݣ�RAMֹͣ��������)
                    ram_rw   <= '1';                -- RAM���ֶ�ģʽ (����Ϊ�ǻ״̬)
                    state    <= "0100";             -- ת��������׶� "0100"
                    ir       <= ram_data;           -- ����RAM������ָ�����ָ��Ĵ��� ir
                    pc       <= pc + 1;             -- ��������� pc ��1��ָ����һ��ָ��
						  
                    --ram_en<='1'; 
						  
						  
                -- ״̬ "0100": ����׶� (ID - Instruction Decode)
                -- ����ir�е�ָ���ȡ�����롢�Ĵ�����š���������
                when "0100" => -- ����׶� --13 ���ֲ������Ӧ��ָ�ȡ�Ĵ����ı��
                    DBC      <= '1';
                    ram_en   <= '0';                -- ����RAM�����źţ�Ϊ���ܵĺ����ô���׼��
                    ram_oe   <= '1';
                    ram_rw   <= '1';
                    state    <= "0101";             -- ת����ִ�н׶� "0101"
                    output   <= ir;                 -- �����ǰָ�output�˿� (���ڵ���)
                    op       := ir(15 downto 11);   -- ��ȡָ���5λ��Ϊ������ op
                    case op is
                        -- ָ��: MOVE Rx, Ry (ry -> rx)
                        -- ��ʽ: 01111 | Rx(3) | Ry(3) | unused(5)
                        when "01111" =>      
                            DBC <= '1';             -- MOVE
                            rx  := ir(10 downto 8); -- Ŀ��Ĵ��� Rx
                            ry  := ir(7 downto 5);  -- Դ�Ĵ��� Ry
                        
                        -- ָ��: ADDU Rz, Rx, Ry (rx+ry -> rz) / SUBU Rz, Rx, Ry (rx-ry -> rz)
                        -- ��ʽ: 11100 | Rx(3) | Ry(3) | Rz(3) | xx | func(2) (01 for ADDU, 11 for SUBU)
                        when "11100" => 
                            DBC <= '1';             -- ADDU / SUBU
                            rx  := ir(10 downto 8); -- Դ�Ĵ���1 Rx
                            ry  := ir(7 downto 5);  -- Դ�Ĵ���2 Ry
                            rz  := ir(4 downto 2);  -- Ŀ��Ĵ��� Rz
                        
                        -- ָ��: BNEZ Rx, offset (Branch if Rx != 0)
                        -- ��ʽ: 00100 | Rx(3) | offset(8)
                        when "00101" =>             -- BNEZ 
                            DBC  <= '1';
                            rx   := ir(10 downto 8); -- �����жϼĴ��� Rx
                            if ir(7) = '0' then
                                imme := "00000000" & ir(7 downto 0);
                            else
                                imme := "11111111" & ir(7 downto 0);
                            end if; -- 8λ������ƫ���� 
                        
                        -- ָ��: LW Ry, offset(Rx) (M[rx+offset] -> ry)
                        -- ��ʽ: 10011 | Rx(3) | Ry(3) | 000 | offset(5)
                        when "10011" =>             -- LW (Load Word)
                            DBC  <= '1';
                            rx   := ir(10 downto 8); -- ��ַ�Ĵ��� Rx
                            ry   := ir(7 downto 5);  -- Ŀ��Ĵ��� Ry
                            imme := "00000000000" & ir(4 downto 0); -- 5λ������ƫ���� 
                            rr(rx, t1);             -- ��ȡ��ַ�Ĵ���Rx��ֵ��t1
                            mar  := t1 + imme;      -- ������Ч�ڴ��ַ: MAR = Rx + offset
                        
                        -- ָ��: XOR Rx, Ry (rx xor ry -> rx) / OR Rx, Ry (rx or ry -> rx)
                        -- ��ʽ: 11101 | Rx(3) | Ry(3) | func_ext(5) (01110 for XOR, 01101 for OR)
                        when "11101" =>             -- XOR / OR
                            DBC <= '1';
                            rx  := ir(10 downto 8); -- Ŀ�꼰Դ�Ĵ���1 Rx
                            ry  := ir(7 downto 5);  -- Դ�Ĵ���2 Ry
                                                    -- ������XOR����OR��ir(4 downto 0)��������ִ�н׶��ж�
                        
                        -- ָ��: SW Ry, offset(Rx) (ry -> M[rx+offset])
                        -- ��ʽ: 11011 | Rx(3) | Ry(3) | 000 | offset(5)
                        when "11011" =>             -- SW (Store Word)
                            DBC  <= '1';
                            rx   := ir(10 downto 8); -- ��ַ�Ĵ��� Rx
                            ry   := ir(7 downto 5);  -- Դ�Ĵ��� Ry (�����ݽ��������ڴ�)
                            imme := "00000000000" & ir(4 downto 0); -- 5λ������ƫ���� (����չ)
                            rr(rx, t1);             -- ��ȡ��ַ�Ĵ���Rx��ֵ��t1
                            rr(ry, t2);             -- ��ȡԴ�Ĵ���Ry��ֵ��t2 (׼��д���ڴ�)
                            mar  := t1 + imme;      -- ������Ч�ڴ��ַ: MAR = Rx + offset

                        -- LI: Rx = imm(8)
                        when "01101" =>             -- LI
                            DBC <= '1';
                            rx   := ir(10 downto 8);
                            imme := "00000000" & ir(7 downto 0);

                        -- ADDIU: Rx = Rx + imm(8)
                        when "01001" =>             -- ADDIU
                            DBC <= '1';
                            rx   := ir(10 downto 8);
                            if ir(7) = '0' then
                                imme := "00000000" & ir(7 downto 0);
                            else
                                imme := "11111111" & ir(7 downto 0);
                            end if;

                        -- BEQZ: if Rx=0 then PC += imm(8)
                        when "00001" =>             -- BEQZ
                            DBC  <= '1';
                            rx   := ir(10 downto 8);
                            if ir(7) = '0' then
                                imme := "00000000" & ir(7 downto 0);
                            else
                                imme := "11111111" & ir(7 downto 0);
                            end if;

                        -- JALR: Ry = PC; PC = Rx
                        when "00010" =>             -- JALR
                            DBC <= '1';
                            rx  := ir(10 downto 8);
                            ry  := ir(7 downto 5);
                        when others =>
                            null; -- δ����Ĳ�����
                    end case;

                -- ״̬ "0101": ִ�н׶� (EX - Execute)
                -- ����������ִ����Ӧ������/�߼�������ַ����
                when "0101" => -- ִ�н׶� 14
                    DBC   <= '1';
                    state <= "0110"; -- ת�����ô�׶� "0110"
                    output <= ir;    -- �����ǰָ�� (���ڵ���)
                    case op is
                        when "11100" => -- ADDU / SUBU
                            if (ir(1 downto 0) = "01") then -- ADDU (Rz = Rx + Ry)
                                rr(rx, t1); rr(ry, t2); -- ��ȡ������ Rx, Ry
                                t3 := t1 + t2;          -- ִ�мӷ���������� t3
                            elsif (ir(1 downto 0) = "10") then -- SUBU (Rz = Rx - Ry)
                                rr(rx, t1); rr(ry, t2); -- ��ȡ������ Rx, Ry
                                t3 := t1 - t2;          -- ִ�м������������ t3
                            elsif (ir(1 downto 0) = "11") then -- SLL (Rz = Rx << Ry)
                                rr(rx, t1); rr(ry, t2);
                                t3 := SHL(t1, t2);
                            else
                                null;
                            end if;
                        when "00101" => -- BNEZ (Branch if Rx ��= 0)
                            DBC <= '1';
                            rr(rx, t1); -- ��ȡ�Ĵ���Rx��ֵ��t1
                            if (t1 /= "0000000000000000") then -- ���Rx ��= 0
                                -- ��ת�߼�: pc <= MAR + imme;
                                -- MAR��ʱ��ֵ��ȡָʱ��PC (����ǰָ���ַ)
                                -- ��תĿ��Ϊ: (��ǰָ���ַ) + 8λƫ����
                            
                                pc <= pc + imme;
										  output <= imme;  
										  
                            end if;
                        when "10011" => -- LW (Load Word)
                            DBC <= '1';
                            ram_addr <= "00" & mar; -- ���÷ô��ַ (��������׶μ���ô���mar)
                                                    -- ʵ�ʵ�RAM����������һ״̬ (�ô�׶�)
                        when "11101" => -- XOR / OR
                            DBC <= '1';
                            if (ir(4 downto 0) = "01110") then -- XOR (Rx = Rx XOR Ry)
                                rr(rx, t1); rr(ry, t2); -- ��ȡ������ Rx, Ry
                                t3 := t1 xor t2;        -- ִ����򣬽������ t3
                            elsif (ir(4 downto 0) = "01101") then -- OR (Rx = Rx OR Ry)
                                rr(rx, t1); rr(ry, t2); -- ��ȡ������ Rx, Ry
                                t3 := t1 or t2;         -- ִ�л򣬽������ t3
                            else 
                                null;
                            end if;
                        when "11011" => -- SW (Store Word)
                            DBC <= '1';
                            ram_addr <= "00" & MAR; -- ���÷ô��ַ (��������׶μ���ô���mar)
                            mbr      := t2;        -- ��Ҫ�����ڴ������ (���ԼĴ���Ry, ��������׶ζ���t2) ����MBR
                                                    -- ʵ�ʵ�RAMд��������һ״̬ (�ô�׶�)
                        when "01101" => -- LI
                            DBC <= '1';
                            t3 := imme;
                        when "01001" => -- ADDIU
                            DBC <= '1';
                            rr(rx, t1);
                            t3 := t1 + imme;
                        when "00001" => -- BEQZ
                            DBC <= '1';
                            rr(rx, t1);
                            if (t1 = "0000000000000000") then
                                pc <= pc + imme;
                                output <= pc + imme;
                            end if;
                        when "00010" => -- JALR
                            DBC <= '1';
                            rr(rx, t1);
                            pc <= t1;
                            t3 := pc;
                        when "01111" => -- MOVE (Rx = Ry)
                            DBC <= '1';
                            rr(ry, t2); -- ��ȡԴ�Ĵ���Ry��ֵ��t2
                            t3  := t2;  -- �������t3��׼����д�ؽ׶�д��Ŀ��Ĵ���Rx
                        when others =>
                            null;
                    end case;

                -- ״̬ "0110": �ô�׶� (MEM - Memory Access)
                -- ����LW��SWָ����ڴ��д����
                when "0110" => -- �ô�׶� 15
                    case op is							
                        when "10011" => -- LW (Load Word)
                            state    <= "1000";             -- LW��Ҫ����һ��״̬("1000")���ȴ����ݴ�RAM����
                            ram_addr <= "00" & MAR;         -- �ٴ�ȷ�Ϸô��ַ (�������ִ࣬�н׶�����)
                            ram_data <= "ZZZZZZZZZZZZZZZZ"; -- CPU�����߸��裬׼������RAM����
                            output   <= mar;                -- ����ô��ַ (���ڵ���)
                            ram_en   <= '0';                -- ʹ��RAM
                            ram_oe   <= '0';                -- RAM���ʹ�� (������)
                            ram_rw   <= '1';                -- RAM��ģʽ
                        when "11011" => -- SW (Store Word)
                            state    <= "0111";             -- SW������ɺ�ֱ�ӽ���д��/��һ��ȡָ�׶�
                            ram_data <= mbr;                -- ��MBR�е�����(���ԼĴ���Ry)�ŵ�����������
                            ram_en   <= '0';                -- ʹ��RAM
                            ram_oe   <= '1';                -- RAM�����ֹ (��ΪCPUҪд����)
                            ram_rw   <= '0';                -- RAMдģʽ
                            output   <= MAR(7 downto 0) & mbr(7 downto 0); -- ������ֵ�ַ������
                        when others => -- �Ƿô�ָ��
                            state  <= "0111";             -- ֱ����ת��д�ؽ׶� "0111"
                            output <= ir;                 -- �����ǰָ�� (���ڵ���)
                    end case;
					
                -- ״̬ "1000": �ô�׶� - LW���ݻ�ȡ
                -- LWָ���ڷ���������󣬵ȴ�RAM����׼���ò���ȡ����
                when "1000" => -- (LW ָ��ȴ����ݴ�RAM���ص�״̬)
                    DBC      <= '1';
                    ram_en   <= '0';                -- RAM����ʹ�� (�����RAMʱ�����)
                    ram_oe   <= '1';                -- RAMֹͣ���������� (CPU׼����������)
                    ram_rw   <= '1';                -- RAM���ֶ�ģʽ (����Ϊ�ǻ)					
                    state    <= "0111";             -- ת����д�ؽ׶� "0111"
                    mbr      := ram_data;           -- ��ram_data��������RAM���ص����ݵ�MBR
                    OUTPUT   <= mbr;                -- ������ڴ���������� (���ڵ���)
			
                -- ״̬ "0111": д�ؽ׶� (WB - Write Back)
                -- ��ִ�н������ڴ���ص�����д�ص���Ӧ��ͨ�üĴ���
                when "0111" => -- д�ؽ׶� 16
                    state  <= "0011";             -- ��ɺ�ص�ȡָ�׶� "0011"
                    mar    := pc;                 -- ����MARΪPC��ֵ��Ϊ��һ��ָ���ȡָ��׼��
                    ram_en <= '0';                -- ��ЩRAM�����źŵ������ƺ���Ϊ��"����"��"׼����һ�ζ�"
                    ram_oe <= '1';                -- RAM�����ֹ
                    ram_rw <= '1';                -- RAM��ģʽ 
                                                  -- ����ȫ������������ ram_en <= '1' (����RAM) �����ǰ���ڲ�����
                    case op is
                        when "11100" => -- ADDU / SUBU	
                            OUTPUT <= T3; -- ��������� (���ڵ���)
                            case rz is -- �����t3д��Ŀ��Ĵ���Rz
                                when "000" => r0 <= t3; when "001" => r1 <= t3;
                                when "010" => r2 <= t3; when "011" => r3 <= t3;
                                when "100" => r4 <= t3; when "101" => r5 <= t3;
                                when "110" => r6 <= t3; when "111" => r7 <= t3;
                                when others => null;
                            end case;
                        when "10011" => -- LW (Load Word)
                            -- OUTPUT<=MAR(7 downto 0)&mbr(7 downto 0); 
                            case ry is -- �����ڴ����MBR������д��Ŀ��Ĵ���Ry
                                when "000" => r0 <= mbr; when "001" => r1 <= mbr;
                                when "010" => r2 <= mbr; when "011" => r3 <= mbr;
                                when "100" => r4 <= mbr; when "101" => r5 <= mbr;
                                when "110" => r6 <= mbr; when "111" => r7 <= mbr;
                                when others => null;
                            end case;
                        when "01101" => -- LI
                            output <= t3;
                            case rx is
                                when "000" => r0 <= t3; when "001" => r1 <= t3;
                                when "010" => r2 <= t3; when "011" => r3 <= t3;
                                when "100" => r4 <= t3; when "101" => r5 <= t3;
                                when "110" => r6 <= t3; when "111" => r7 <= t3;
                                when others => null;
                            end case;
                        when "01001" => -- ADDIU
                            output <= t3;
                            case rx is
                                when "000" => r0 <= t3; when "001" => r1 <= t3;
                                when "010" => r2 <= t3; when "011" => r3 <= t3;
                                when "100" => r4 <= t3; when "101" => r5 <= t3;
                                when "110" => r6 <= t3; when "111" => r7 <= t3;
                                when others => null;
                            end case;
                        when "00010" => -- JALR
                            output <= t3;
                            case ry is
                                when "000" => r0 <= t3; when "001" => r1 <= t3;
                                when "010" => r2 <= t3; when "011" => r3 <= t3;
                                when "100" => r4 <= t3; when "101" => r5 <= t3;
                                when "110" => r6 <= t3; when "111" => r7 <= t3;
                                when others => null;
                            end case;
                        when "01111" => -- MOVE
                            output <= t3; -- ����ƶ������� (���ڵ���)
                            case rx is -- ��t3 (����Դ�Ĵ���Ry) д��Ŀ��Ĵ���Rx
                                when "000" => r0 <= t3; when "001" => r1 <= t3;
                                when "010" => r2 <= t3; when "011" => r3 <= t3;
                                when "100" => r4 <= t3; when "101" => r5 <= t3;
                                when "110" => r6 <= t3; when "111" => r7 <= t3;
                                when others => null;
                            end case;
                        when "11101" => -- XOR / OR
                            output <= t3; -- ��������� (���ڵ���)
                            case rx is -- �����t3д��Ŀ��Ĵ���Rx (������Щָ�Rx��Ŀ���Դ֮һ)
                                when "000" => r0 <= t3; when "001" => r1 <= t3;
                                when "010" => r2 <= t3; when "011" => r3 <= t3;
                                when "100" => r4 <= t3; when "101" => r5 <= t3;
                                when "110" => r6 <= t3; when "111" => r7 <= t3;
                                when others => null;
                            end case;
                        when others =>
                            null; -- ����ָ����д�ؽ׶��޲���
                    end case;
                when others => -- ���state����δ�����ֵ
                    state <= "0000"; -- Ĭ�ϻص���ʼ״̬ "0000"
            end case;
        end if;
    end process; -- �����ƽ��̽���
	
    -- �ڶ������̣�����߼������������߶���������seg
    -- ����CPU�ĵ�ǰ״̬state�������ͬ�ı��뵽seg�˿�
    process (state)
    begin
        case state is
            -- ״̬�������߶��������ʾ���ݵ�ӳ��
            -- �����14λseg���������������7������ܣ��ֱ���ʾ��λ���ֻ��ַ�
            -- ���� "01111110111111" ���ܴ��� "00" (�����7λһ������ܣ���7λһ��)
            when "0000" => seg <= "01111110111111"; -- ״̬ 00 (��ʼ/ģʽѡ��)
            when "0001" => seg <= "01111110000110"; -- ״̬ 01 (RAMд��ַ)
            when "0010" => seg <= "01111111011011"; -- ״̬ 02 (RAMд����)
            when "0011" => seg <= "00001100000110"; -- ״̬ 11 (ȡָ1 - ����ַ)
            when "1111" => seg <= "00001101011011"; -- ״̬ 12 (ȡָ2 - ��ָ��) (ע����״̬��"1111"����������Ӧ����)
            when "0100" => seg <= "00001101001111"; -- ״̬ 13 (����)
            when "0101" => seg <= "00001101100110"; -- ״̬ 14 (ִ��)
            when "0110" => seg <= "00001101101101"; -- ״̬ 15 (�ô�)
            when "0111" => seg <= "00001101111100"; -- ״̬ 16 (д��)
				when "1001" => seg <= "10110110000110"; -- ״̬ 21 (�ж϶�ȡ����/RAM)
				when "1010" => seg <= "10110111011011"; -- ״̬ 22 (�����ȡ��ַ)
				when "1011" => seg <= "10110111001111"; -- ״̬ 23 (�����������)
				when "1100" => seg <= "10110111100110"; -- ״̬ 24 (���RAM����)
            -- ע�⣺״̬ "1000" (LW�ô�ĵڶ�����) ������û�ж�Ӧ��seg�������
            -- �������״̬"1000"��seg��������һ�����ڵ�ֵ
            when others =>
                NULL; -- ����δ����״̬��seg������ı��ȷ��
        end case;
    end process; -- seg�������̽���
	
end Behavioral; -- �ܹ������
