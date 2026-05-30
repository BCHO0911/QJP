-- ============================================================
-- 存储器实验 - 测试激励文件
-- 使用快速节拍(TICK_DIV=50)以加快仿真速度
-- ============================================================
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;

entity ram_tb is
end ram_tb;

architecture Behavioral of ram_tb is

    component ram_exp
        generic (
            TICK_DIV : integer := 500000
        );
        Port (
            CLK        : in  STD_LOGIC;
            RST        : in  STD_LOGIC;
            ctrl_r     : in  STD_LOGIC;
            Input_data : in  STD_LOGIC_VECTOR (15 downto 0);
            LIGHT      : out STD_LOGIC_VECTOR (15 downto 0);
            ADDR       : out STD_LOGIC_VECTOR (15 downto 0);
            DATA       : inout STD_LOGIC_VECTOR (15 downto 0);
            RAM1_EN    : out STD_LOGIC;
            RAM1_WE    : out STD_LOGIC;
            RAM1_OE    : out STD_LOGIC;
            DBC        : out STD_LOGIC
        );
    end component;

    -- 模拟 SRAM 存储阵列
    type ram_array is array (0 to 65535) of STD_LOGIC_VECTOR (15 downto 0);
    shared variable sram : ram_array := (others => (others => '0'));

    signal t_clk        : STD_LOGIC := '0';
    signal t_rst        : STD_LOGIC := '0';
    signal t_ctrl_r     : STD_LOGIC := '0';
    signal t_input_data : STD_LOGIC_VECTOR (15 downto 0) := x"0000";
    signal t_light      : STD_LOGIC_VECTOR (15 downto 0);
    signal t_addr       : STD_LOGIC_VECTOR (15 downto 0);
    signal t_data       : STD_LOGIC_VECTOR (15 downto 0);
    signal t_ram1_en    : STD_LOGIC;
    signal t_ram1_we    : STD_LOGIC;
    signal t_ram1_oe    : STD_LOGIC;
    signal t_dbc        : STD_LOGIC;

    -- 时钟周期 20ns (50MHz)
    constant CLK_PERIOD : time := 20 ns;

begin

    -- 实例化待测模块，使用快速节拍加快仿真
    UUT: ram_exp
        generic map (TICK_DIV => 50)
        port map (
            CLK        => t_clk,
            RST        => t_rst,
            ctrl_r     => t_ctrl_r,
            Input_data => t_input_data,
            LIGHT      => t_light,
            ADDR       => t_addr,
            DATA       => t_data,
            RAM1_EN    => t_ram1_en,
            RAM1_WE    => t_ram1_we,
            RAM1_OE    => t_ram1_oe,
            DBC        => t_dbc
        );

    -- 时钟生成
    t_clk <= not t_clk after CLK_PERIOD / 2;

    -- ========================================================
    -- 模拟 SRAM 行为（异步 SRAM）
    -- 写操作：当 WE 和 EN 有效时写入
    -- 读操作：当 OE 和 EN 有效时，SRAM 驱动数据到总线
    -- ========================================================

    -- SRAM 写过程
    sram_write : process(t_addr, t_data, t_ram1_en, t_ram1_we)
    begin
        if t_ram1_en = '1' and t_ram1_we = '1' then
            sram(conv_integer(t_addr)) := t_data;
        end if;
    end process sram_write;

    -- SRAM 读驱动（仅在读操作时驱动总线，写操作时高阻）
    sram_read : process(t_addr, t_ram1_en, t_ram1_oe, t_ram1_we)
    begin
        if t_ram1_en = '1' and t_ram1_oe = '1' and t_ram1_we = '0' then
            t_data <= sram(conv_integer(t_addr));
        else
            t_data <= (others => 'Z');
        end if;
    end process sram_read;

    -- ========================================================
    -- 测试流程
    -- ========================================================
    stim_proc : process
    begin
        -- 初始复位
        t_rst        <= '0';
        t_ctrl_r     <= '0';
        t_input_data <= x"0000";
        wait for 100 ns;

        -- 释放复位
        t_rst <= '1';
        wait for 100 ns;

        -- ================================================
        -- 第一部分：写 RAM - 连续写 10 个数到地址 0~9
        -- 每次通过修改 Input_data 来改变写入的地址和数据
        -- ================================================
        t_ctrl_r <= '0';  -- 写模式

        -- 写地址0: 数据 0x0001
        t_input_data <= x"0001";
        wait for 3 * 50 * CLK_PERIOD;

        -- 写地址1: 数据 0x0002
        t_input_data <= x"0002";
        wait for 3 * 50 * CLK_PERIOD;

        -- 写地址2: 数据 0x0003
        t_input_data <= x"0003";
        wait for 3 * 50 * CLK_PERIOD;

        -- 写地址3: 数据 0x0004
        t_input_data <= x"0004";
        wait for 3 * 50 * CLK_PERIOD;

        -- 写地址4: 数据 0x0005
        t_input_data <= x"0005";
        wait for 3 * 50 * CLK_PERIOD;

        -- 写地址5: 数据 0x0006
        t_input_data <= x"0006";
        wait for 3 * 50 * CLK_PERIOD;

        -- 写地址6: 数据 0x0007
        t_input_data <= x"0007";
        wait for 3 * 50 * CLK_PERIOD;

        -- 写地址7: 数据 0x0008
        t_input_data <= x"0008";
        wait for 3 * 50 * CLK_PERIOD;

        -- 写地址8: 数据 0x0009
        t_input_data <= x"0009";
        wait for 3 * 50 * CLK_PERIOD;

        -- 写地址9: 数据 0x000A
        t_input_data <= x"000A";
        wait for 3 * 50 * CLK_PERIOD;

        -- 写完成后等待观察
        wait for 5 * 50 * CLK_PERIOD;

        -- ================================================
        -- 第二部分：读 RAM - 切换到读模式逐个读出
        -- ================================================
        t_ctrl_r <= '1';  -- 读模式

        -- 等待读完 10 个单元
        wait for 10 * 3 * 50 * CLK_PERIOD;

        -- 读完回到空闲，等待观察
        wait for 5 * 50 * CLK_PERIOD;

        -- ================================================
        -- 第三部分：用不同数据再次验证
        -- ================================================
        t_rst <= '0';
        wait for 100 ns;
        t_rst <= '1';
        wait for 100 ns;

        -- 写入一组特殊数据
        t_ctrl_r <= '0';  -- 写模式

        t_input_data <= x"AA55";
        wait for 3 * 50 * CLK_PERIOD;

        t_input_data <= x"1234";
        wait for 3 * 50 * CLK_PERIOD;

        t_input_data <= x"FFFF";
        wait for 3 * 50 * CLK_PERIOD;

        t_input_data <= x"00FF";
        wait for 3 * 50 * CLK_PERIOD;

        t_input_data <= x"55AA";
        wait for 3 * 50 * CLK_PERIOD;

        wait for 5 * 50 * CLK_PERIOD;

        -- 读出验证
        t_ctrl_r <= '1';  -- 读模式
        wait for 5 * 3 * 50 * CLK_PERIOD;

        wait;
    end process stim_proc;

end Behavioral;
