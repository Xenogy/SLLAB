CREATE TABLE IF NOT EXISTS public.hardware
(
    id SERIAL PRIMARY KEY,                                          -- Auto-incrementing integer ID (Primary Key)
    acc_id TEXT NOT NULL REFERENCES accounts(acc_id),               -- Account identifier (String)
    bios_vendor TEXT,                                               -- BIOS Vendor (String)
    bios_version VARCHAR(50),                                       -- BIOS Version (String, limited length)
    disk_serial VARCHAR(100),                                       -- Disk Serial Number (String, limited length)
    disk_model VARCHAR(100),                                        -- Disk Model (String, limited length)
    smbios_uuid UUID,                                               -- SMBIOS UUID (Universally Unique Identifier)
    mb_manufacturer TEXT,                                           -- Motherboard Manufacturer (String)
    mb_product TEXT,                                                -- Motherboard Product Name (String)
    mb_version VARCHAR(50),                                         -- Motherboard Version (String, limited length)
    mb_serial VARCHAR(100),                                         -- Motherboard Serial Number (String, limited length)
    mac_address VARCHAR(17),                                        -- MAC Address (String, format XX:XX:XX:XX:XX:XX)
    vmid INTEGER,                                                   -- VM ID (Integer)
    pcname VARCHAR(100),                                            -- PC Name / Hostname (String, limited length)
    machine_guid UUID,                                              -- Machine GUID (Universally Unique Identifier)
    hwprofile_guid UUID,                                            -- Hardware Profile GUID (Universally Unique Identifier)
    product_id VARCHAR(32),                                         -- Product ID (String)
    device_id UUID                                                  -- Device ID (Universally Unique Identifier)
);

COMMENT ON COLUMN public.hardware.id IS 'Unique auto-incrementing identifier for the hardware record';
COMMENT ON COLUMN public.hardware.acc_id IS 'Associated account identifier';
COMMENT ON COLUMN public.hardware.bios_vendor IS 'Vendor of the system BIOS';
COMMENT ON COLUMN public.hardware.bios_version IS 'Version of the system BIOS';
COMMENT ON COLUMN public.hardware.disk_serial IS 'Serial number of the primary disk drive';
COMMENT ON COLUMN public.hardware.disk_model IS 'Model name of the primary disk drive';
COMMENT ON COLUMN public.hardware.smbios_uuid IS 'System Management BIOS universally unique identifier';
COMMENT ON COLUMN public.hardware.mb_manufacturer IS 'Manufacturer of the motherboard';
COMMENT ON COLUMN public.hardware.mb_product IS 'Product name of the motherboard';
COMMENT ON COLUMN public.hardware.mb_version IS 'Version of the motherboard';
COMMENT ON COLUMN public.hardware.mb_serial IS 'Serial number of the motherboard';
COMMENT ON COLUMN public.hardware.mac_address IS 'Primary MAC address of the network interface';
COMMENT ON COLUMN public.hardware.vmid IS 'Virtual Machine identifier (if applicable)';
COMMENT ON COLUMN public.hardware.pcname IS 'Hostname or PC name of the machine';
COMMENT ON COLUMN public.hardware.machine_guid IS 'Unique identifier for the machine (e.g., from OS)';
COMMENT ON COLUMN public.hardware.hwprofile_guid IS 'Hardware Profile globally unique identifier (e.g., from Windows)';
COMMENT ON COLUMN public.hardware.product_id IS 'Product identifier (e.g., from Windows)';
COMMENT ON COLUMN public.hardware.device_id IS 'Unique identifier for the device (e.g., from Windows)';

CREATE INDEX idx_hardware_acc_id ON public.hardware (acc_id);
CREATE INDEX idx_hardware_mac_address ON public.hardware (mac_address);
CREATE INDEX idx_hardware_smbios_uuid ON public.hardware (smbios_uuid);

ALTER TABLE IF EXISTS public.hardware
    OWNER to ps_user;

GRANT ALL ON TABLE public.hardware TO acc_user;
GRANT ALL ON TABLE public.hardware TO ps_user;

-- Grant sequence permissions
GRANT USAGE, SELECT ON SEQUENCE hardware_id_seq TO acc_user;
GRANT USAGE, SELECT ON SEQUENCE hardware_id_seq TO ps_user;