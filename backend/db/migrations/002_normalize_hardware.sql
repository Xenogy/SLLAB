-- Migration: Normalize Hardware Table

-- Start a transaction
BEGIN;

-- 1. Create a new normalized hardware table
CREATE TABLE IF NOT EXISTS public.hardware_normalized (
    id SERIAL PRIMARY KEY,
    account_id TEXT REFERENCES public.accounts_normalized(account_id),
    bios_vendor TEXT,
    bios_version VARCHAR(50),
    disk_serial VARCHAR(100),
    disk_model VARCHAR(100),
    smbios_uuid UUID,
    motherboard_manufacturer TEXT,
    motherboard_product TEXT,
    motherboard_version VARCHAR(50),
    motherboard_serial VARCHAR(100),
    mac_address VARCHAR(17),
    vm_id INTEGER,
    pc_name VARCHAR(100),
    machine_guid UUID,
    hardware_profile_guid UUID,
    product_id VARCHAR(32),
    device_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    owner_id INTEGER NOT NULL REFERENCES public.users(id)
);

COMMENT ON TABLE public.hardware_normalized IS 'Normalized hardware table';
COMMENT ON COLUMN public.hardware_normalized.id IS 'Auto-incrementing ID (Primary Key)';
COMMENT ON COLUMN public.hardware_normalized.account_id IS 'Associated account identifier';
COMMENT ON COLUMN public.hardware_normalized.bios_vendor IS 'Vendor of the system BIOS';
COMMENT ON COLUMN public.hardware_normalized.bios_version IS 'Version of the system BIOS';
COMMENT ON COLUMN public.hardware_normalized.disk_serial IS 'Serial number of the primary disk drive';
COMMENT ON COLUMN public.hardware_normalized.disk_model IS 'Model name of the primary disk drive';
COMMENT ON COLUMN public.hardware_normalized.smbios_uuid IS 'System Management BIOS universally unique identifier';
COMMENT ON COLUMN public.hardware_normalized.motherboard_manufacturer IS 'Manufacturer of the motherboard';
COMMENT ON COLUMN public.hardware_normalized.motherboard_product IS 'Product name of the motherboard';
COMMENT ON COLUMN public.hardware_normalized.motherboard_version IS 'Version of the motherboard';
COMMENT ON COLUMN public.hardware_normalized.motherboard_serial IS 'Serial number of the motherboard';
COMMENT ON COLUMN public.hardware_normalized.mac_address IS 'Primary MAC address of the network interface';
COMMENT ON COLUMN public.hardware_normalized.vm_id IS 'Virtual Machine identifier (if applicable)';
COMMENT ON COLUMN public.hardware_normalized.pc_name IS 'Hostname or PC name of the machine';
COMMENT ON COLUMN public.hardware_normalized.machine_guid IS 'Unique identifier for the machine (e.g., from OS)';
COMMENT ON COLUMN public.hardware_normalized.hardware_profile_guid IS 'Hardware Profile globally unique identifier (e.g., from Windows)';
COMMENT ON COLUMN public.hardware_normalized.product_id IS 'Product identifier (e.g., from Windows)';
COMMENT ON COLUMN public.hardware_normalized.device_id IS 'Unique identifier for the device (e.g., from Windows)';
COMMENT ON COLUMN public.hardware_normalized.created_at IS 'When the hardware record was created';
COMMENT ON COLUMN public.hardware_normalized.updated_at IS 'When the hardware record was last updated';
COMMENT ON COLUMN public.hardware_normalized.owner_id IS 'User who owns this hardware record';

-- 2. Create indexes for the new hardware table
CREATE INDEX idx_hardware_normalized_account_id ON public.hardware_normalized(account_id);
CREATE INDEX idx_hardware_normalized_mac_address ON public.hardware_normalized(mac_address);
CREATE INDEX idx_hardware_normalized_smbios_uuid ON public.hardware_normalized(smbios_uuid);
CREATE INDEX idx_hardware_normalized_owner_id ON public.hardware_normalized(owner_id);

-- 3. Migrate data from the old hardware table to the new one
INSERT INTO public.hardware_normalized (
    account_id,
    bios_vendor,
    bios_version,
    disk_serial,
    disk_model,
    smbios_uuid,
    motherboard_manufacturer,
    motherboard_product,
    motherboard_version,
    motherboard_serial,
    mac_address,
    vm_id,
    pc_name,
    machine_guid,
    hardware_profile_guid,
    product_id,
    device_id,
    owner_id
)
SELECT
    acc_id,
    bios_vendor,
    bios_version,
    disk_serial,
    disk_model,
    smbios_uuid,
    mb_manufacturer,
    mb_product,
    mb_version,
    mb_serial,
    mac_address,
    vmid,
    pcname,
    machine_guid,
    hwprofile_guid,
    product_id,
    device_id,
    owner_id
FROM public.hardware;

-- 4. Enable RLS on the new hardware table
ALTER TABLE public.hardware_normalized ENABLE ROW LEVEL SECURITY;

-- 5. Create RLS policies for the new hardware table
CREATE POLICY hardware_normalized_user_policy ON public.hardware_normalized
    FOR ALL
    TO acc_user
    USING (owner_id = current_setting('app.current_user_id')::INTEGER);

CREATE POLICY hardware_normalized_admin_policy ON public.hardware_normalized
    FOR ALL
    TO acc_user
    USING (current_setting('app.current_user_role')::TEXT = 'admin');

-- 6. Create a view for RLS
CREATE OR REPLACE VIEW public.hardware_normalized_with_rls AS
SELECT * FROM public.hardware_normalized;

-- 7. Grant permissions on the new hardware table and view
GRANT ALL ON TABLE public.hardware_normalized TO acc_user;
GRANT ALL ON TABLE public.hardware_normalized_with_rls TO acc_user;

-- 8. Create a trigger to update the timestamp
CREATE TRIGGER update_hardware_normalized_timestamp
BEFORE UPDATE ON public.hardware_normalized
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- Commit the transaction
COMMIT;
