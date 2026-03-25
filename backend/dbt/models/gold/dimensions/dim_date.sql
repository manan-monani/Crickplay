-- Dimension: Date
-- Standard date dimension table using dbt_utils date_spine
-- Facilitates time-series slicing by year, month, day, tournament window

{{
    config(
        materialized='table',
        schema='gold'
    )
}}


with date_spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2018-01-01' as date)",
        end_date="cast('2027-12-31' as date)"
    ) }}
),

dates as (
    select
        cast(date_day as date) as date_key
    from date_spine
)

select
    -- Primary key
    date_key,

    -- Date components
    extract(year from date_key)::int as year,
    extract(month from date_key)::int as month,
    extract(day from date_key)::int as day_of_month,
    extract(dow from date_key)::int as day_of_week_num,  -- 0=Sun, 6=Sat

    -- Day name
    to_char(date_key, 'Day') as day_name,
    to_char(date_key, 'Mon') as month_short,
    to_char(date_key, 'Month') as month_name,

    -- Quarter
    extract(quarter from date_key)::int as quarter,
    'Q' || extract(quarter from date_key)::text as quarter_label,

    -- Week
    extract(week from date_key)::int as week_of_year,

    -- Weekend flag
    case
        when extract(dow from date_key) in (0, 6) then true
        else false
    end as is_weekend,

    -- T20 World Cup 2026 window flags (estimated Oct-Nov 2026)
    case
        when date_key between '2026-10-01' and '2026-11-30' then true
        else false
    end as is_wc_2026_window,

    -- Tournament phase mapping (approximate based on WC schedule)
    case
        when date_key between '2026-10-01' and '2026-10-15' then 'Group Stage'
        when date_key between '2026-10-16' and '2026-10-25' then 'Super 8'
        when date_key between '2026-10-26' and '2026-10-30' then 'Semi-final'
        when date_key between '2026-10-31' and '2026-11-02' then 'Final'
        else null
    end as tournament_phase,

    -- ISO format
    to_char(date_key, 'YYYY-MM-DD') as date_iso,
    to_char(date_key, 'YYYYMMDD')::int as date_int_key,

    -- Cricket season approximation
    case
        when extract(month from date_key) between 1 and 3 then 'Winter'
        when extract(month from date_key) between 4 and 6 then 'IPL/Spring'
        when extract(month from date_key) between 7 and 9 then 'Summer'
        else 'Autumn/T20WC'
    end as cricket_season,

    -- Record metadata
    current_timestamp as loaded_at

from dates
