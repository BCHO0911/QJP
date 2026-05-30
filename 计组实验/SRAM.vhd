library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;
use IEEE.STD_LOGIC_ARITH.ALL;

entity alu is
    Port ( 
        clk : in  STD_LOGIC;       
        rst : in  STD_LOGIC;       
        DATA : inout STD_LOGIC_VECTOR(15 downto 0);
        ADDR : out STD_LOGIC_VECTOR(15 downto 0);
        INPUT : in STD_LOGIC_VECTOR(15 downto 0);  
        OUTPUT : out STD_LOGIC_VECTOR(15 downto 0);
        RAM1_EN : out  STD_LOGIC;
        RAM1_OE : out  STD_LOGIC;
        RAM1_WE : out  STD_LOGIC;
        dbc : out  STD_LOGIC;
        stateCnt : out STD_LOGIC_VECTOR(6 downto 0)
    );
end alu;

architecture Behavioral of alu is
    signal state: integer range 0 to 6;
    signal tmp_addr : STD_LOGIC_VECTOR(15 downto 0);
    signal tmp_data : STD_LOGIC_VECTOR(15 downto 0);

begin

process(rst, clk)
begin

    -- ??
    if (rst = '0' ) then 

        state <= 0; 

        tmp_addr <= (others => '0');
        tmp_data <= (others => '0');

        ADDR <= (others => '0');

        DATA <= (others => 'Z');

        RAM1_EN <= '1';
        RAM1_OE <= '1';
        RAM1_WE <= '1';

        OUTPUT <= (others=>'0'); 

        stateCnt <= not "1000000";  -- ??0

    elsif (clk'event and clk = '1') then

        case state is

            -- ??0
            when 0 => 

                state <= 1; 

                tmp_addr <= INPUT;

                stateCnt <= not "1111001";  -- ??1

                OUTPUT <= INPUT;


            -- ??1
            when 1 => 

                state <= 2; 

                tmp_data <= INPUT;

                stateCnt <= not "0100100";  -- ??2

                OUTPUT <= INPUT;


            -- ??2
            when 2 => 

                state <= 3; 

                RAM1_EN <= '0';
                RAM1_OE <= '1';
                RAM1_WE <= '0';

                ADDR <= tmp_addr;

                DATA <= tmp_data;

                stateCnt <= not "0110000";  -- ??3

                OUTPUT <= tmp_data;


            -- ??3
            when 3 => 

                state <= 4; 

                RAM1_WE <= '1';
                RAM1_EN <= '1';

                DATA <= (others => 'Z');

                stateCnt <= not "0011001";  -- ??4

                OUTPUT <= tmp_data;


            -- ??4
            when 4 => 

                state <= 5; 

                tmp_addr <= INPUT;

                stateCnt <= not "0010010";  -- ??5

                OUTPUT <= INPUT;


            -- ??5
            when 5 => 

                state <= 6; 

                RAM1_EN <= '0';
                RAM1_OE <= '0';
                RAM1_WE <= '1';

                ADDR <= tmp_addr;

                stateCnt <= not "0000010";  -- ??6

                OUTPUT <= DATA;


            -- ??6
            when 6 => 

                state <= 0; 

                RAM1_OE <= '1';
                RAM1_EN <= '1';

                stateCnt <= not "1000000";  -- ??0

                OUTPUT <= DATA;

        end case;

    end if;

    dbc <= '1';

end process;

end Behavioral;