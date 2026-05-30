-- ============================================================
-- 存储器实验：SRAM 读写控制
-- 采用状态机控制 RAM 的读写过程，通过拨码开关写入数据，
-- LED 显示地址和数据
-- ============================================================
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;

entity ram_exp is
    generic (
        TICK_DIV : integer := 500000   -- 节拍分频系数，50MHz/500000=10ms
                                       -- 仿真时可改为 50 以加快仿真
    );
    Port (
        CLK        : in  STD_LOGIC;                     -- 系统时钟 50MHz
        RST        : in  STD_LOGIC;                     -- 复位(低电平有效)
        ctrl_r     : in  STD_LOGIC;                     -- 控制信号: '0'=写模式 '1'=读模式
        Input_data : in  STD_LOGIC_VECTOR (15 downto 0); -- 拨码开关输入(地址/数据)
        LIGHT      : out STD_LOGIC_VECTOR (15 downto 0); -- LED 显示
        ADDR       : out STD_LOGIC_VECTOR (15 downto 0); -- RAM 地址线
        DATA       : inout STD_LOGIC_VECTOR (15 downto 0); -- RAM 数据线(双向)
        RAM1_EN    : out STD_LOGIC;                     -- RAM 片选使能
        RAM1_WE    : out STD_LOGIC;                     -- RAM 写使能
        RAM1_OE    : out STD_LOGIC;                     -- RAM 读使能
        DBC        : out STD_LOGIC                      -- 数码管位选(未用)
    );
end ram_exp;

architecture Behavioral of ram_exp is

    -- 读写控制状态机：决定当前处于写还是读
    -- 内存读写周期状态机：根据时钟控制读写过程
    type state_type is (
        S_IDLE,         -- 空闲等待
        S_WR_SETUP,     -- 写准备：锁存地址和数据
        S_WR_EXEC,      -- 写执行：向 RAM 写入
        S_WR_DISPLAY,   -- 写显示：LED 显示写入的地址和数据
        S_RD_SETUP,     -- 读准备：设置读地址
        S_RD_EXEC,      -- 读执行：从 RAM 读取
        S_RD_DISPLAY    -- 读显示：LED 显示读出的数据
    );
    signal cur_state : state_type := S_IDLE;

    signal addr_reg   : STD_LOGIC_VECTOR (15 downto 0) := x"0000";
    signal data_reg   : STD_LOGIC_VECTOR (15 downto 0) := x"0000";
    signal read_data  : STD_LOGIC_VECTOR (15 downto 0) := x"0000";
    signal count_reg  : STD_LOGIC_VECTOR (15 downto 0) := x"0000";

    -- 分频计数器，产生约 10ms 的节拍信号，便于观察
    signal tick_cnt   : STD_LOGIC_VECTOR (18 downto 0) := (others => '0');
    signal tick_10ms  : STD_LOGIC := '0';

    -- 状态指示灯：LIGHT[15] 用来指示系统是否在工作
    -- 空闲=常亮，写模式=灭，读模式=闪烁
    signal light15    : STD_LOGIC := '1';
    signal rd_blink   : STD_LOGIC := '1';  -- 读模式闪烁翻转

begin

    -- ========================================================
    -- 节拍发生器：50MHz / 500000 ≈ 10ms
    -- ========================================================
    tick_gen : process(CLK, RST)
    begin
        if RST = '0' then
            tick_cnt  <= (others => '0');
            tick_10ms <= '0';
        elsif rising_edge(CLK) then
            if tick_cnt = TICK_DIV - 1 then
                tick_cnt  <= (others => '0');
                tick_10ms <= '1';
            else
                tick_cnt  <= tick_cnt + 1;
                tick_10ms <= '0';
            end if;
        end if;
    end process tick_gen;

    -- ========================================================
    -- 主状态机：包含读写控制和内存读写周期
    -- ========================================================
    main_proc : process(CLK, RST)
    begin
        if RST = '0' then
            cur_state <= S_IDLE;
            addr_reg  <= x"0000";
            data_reg  <= x"0000";
            read_data <= x"0000";
            count_reg <= x"0000";
            light15   <= '1';
            rd_blink  <= '1';
        elsif rising_edge(CLK) then
            if tick_10ms = '1' then
                case cur_state is

                    -- ========== 空闲状态 ==========
                    when S_IDLE =>
                        light15 <= '1';  -- 运行指示灯亮
                        if ctrl_r = '0' then
                            -- 写模式：锁存当前开关数据，准备写入
                            addr_reg <= Input_data;
                            data_reg <= Input_data;
                            cur_state <= S_WR_SETUP;
                        else
                            -- 读模式：从地址 0 开始读取
                            addr_reg  <= x"0000";
                            count_reg <= x"0000";
                            cur_state <= S_RD_SETUP;
                        end if;

                    -- ========== 写准备 ==========
                    when S_WR_SETUP =>
                        light15 <= '0';  -- 写模式指示灯灭
                        cur_state <= S_WR_EXEC;

                    -- ========== 写执行：完成一个写周期 ==========
                    when S_WR_EXEC =>
                        light15 <= '0';
                        cur_state <= S_WR_DISPLAY;

                    -- ========== 写显示 ==========
                    when S_WR_DISPLAY =>
                        light15 <= '0';
                        if ctrl_r = '0' then
                            -- 保持写模式，等待用户修改开关数据
                            cur_state <= S_IDLE;
                        else
                            -- 切换到读模式，从地址 0 开始读
                            addr_reg  <= x"0000";
                            count_reg <= x"0000";
                            cur_state <= S_RD_SETUP;
                        end if;

                    -- ========== 读准备 ==========
                    when S_RD_SETUP =>
                        rd_blink <= not rd_blink;  -- 读模式闪烁
                        light15 <= rd_blink;
                        if count_reg >= x"000A" then
                            -- 已读完 10 个单元(地址 0~9)，回到空闲
                            cur_state <= S_IDLE;
                        else
                            cur_state <= S_RD_EXEC;
                        end if;

                    -- ========== 读执行：完成一个读周期 ==========
                    when S_RD_EXEC =>
                        light15 <= rd_blink;
                        -- 在节拍到来前 DATA 已连接到 read_data，此时锁存
                        read_data <= DATA;
                        count_reg <= count_reg + 1;
                        addr_reg  <= addr_reg + 1;
                        cur_state <= S_RD_DISPLAY;

                    -- ========== 读显示 ==========
                    when S_RD_DISPLAY =>
                        light15 <= rd_blink;
                        -- 显示一个节拍后继续读下一个
                        cur_state <= S_RD_SETUP;

                    when others =>
                        cur_state <= S_IDLE;

                end case;
            end if;
        end if;
    end process main_proc;

    -- ========================================================
    -- 组合输出逻辑：根据当前状态产生 RAM 控制信号和 LED 显示
    -- ========================================================
    comb_out : process(cur_state, addr_reg, data_reg, read_data, Input_data)
    begin
        -- 默认输出
        ADDR    <= (others => '0');
        DATA    <= (others => 'Z');  -- 默认高阻，读RAM时由外部SRAM驱动
        RAM1_EN <= '0';
        RAM1_WE <= '0';
        RAM1_OE <= '0';
        LIGHT   <= (others => '0');

        case cur_state is
            when S_IDLE =>
                -- 空闲时显示当前开关数据
                LIGHT <= Input_data;

            when S_WR_SETUP =>
                -- 准备写入：输出地址和数据到 RAM 端口
                ADDR    <= addr_reg;
                DATA    <= data_reg;
                RAM1_EN <= '1';
                -- LED 显示：高8位=数据高8位, 低8位=地址低8位
                LIGHT   <= data_reg(15 downto 8) & addr_reg(7 downto 0);

            when S_WR_EXEC =>
                -- 执行写入：片选+写使能有效
                ADDR    <= addr_reg;
                DATA    <= data_reg;
                RAM1_EN <= '1';
                RAM1_WE <= '1';
                LIGHT   <= data_reg(15 downto 8) & addr_reg(7 downto 0);

            when S_WR_DISPLAY =>
                -- 写入完成显示：保持地址和数据
                ADDR    <= addr_reg;
                DATA    <= data_reg;
                RAM1_EN <= '1';
                LIGHT   <= data_reg(15 downto 8) & addr_reg(7 downto 0);

            when S_RD_SETUP =>
                -- 准备读取：输出地址，数据线高阻由SRAM驱动
                ADDR    <= addr_reg;
                RAM1_EN <= '1';
                RAM1_OE <= '1';
                -- LED 显示当前要读的地址
                LIGHT   <= x"00" & addr_reg(7 downto 0);

            when S_RD_EXEC =>
                -- 执行读取：片选+读使能有效
                ADDR    <= addr_reg;
                RAM1_EN <= '1';
                RAM1_OE <= '1';
                LIGHT   <= x"00" & addr_reg(7 downto 0);

            when S_RD_DISPLAY =>
                -- 读取完成显示：高8位=读出数据高8位, 低8位=地址低8位
                ADDR    <= addr_reg;
                RAM1_EN <= '1';
                RAM1_OE <= '1';
                LIGHT   <= read_data(15 downto 8) & addr_reg(7 downto 0);

            when others =>
                null;
        end case;
    end process comb_out;

    -- 数码管位选未使用，置低
    DBC <= '0';

end Behavioral;
